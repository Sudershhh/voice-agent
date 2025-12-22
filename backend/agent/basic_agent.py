"""Basic LiveKit agent that can join a room and handle connections."""

import asyncio
import json
import os
import time
from livekit import rtc
from livekit.agents import (
    JobContext,
    cli,
    stt,
    tts,
    
)
from livekit.plugins import openai
from langchain_openai import ChatOpenAI
from agent.langchain_agent import create_paradise_agent, get_agent_response


async def entrypoint(ctx: JobContext):
    """Entry point for the agent when it joins a room."""
    
    try:
        await ctx.connect()
    except Exception as e:
        raise
    
    try:
        participant = await ctx.wait_for_participant()
    except RuntimeError as e:
        raise
    
    participant = list(ctx.room.remote_participants.values())[0]
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
    )
    
    use_rag = bool(os.getenv("PINECONE_API_KEY"))
    
    use_tools = bool(os.getenv("SERPAPI_API_KEY") or os.getenv("GOOGLE_PLACES_API_KEY"))
    
    announcement_queue = asyncio.Queue()
    
    def announce_tool_usage(text: str):
        """Put announcement in queue for async processing."""
        try:
            announcement_queue.put_nowait(text)
        except Exception as e:
            pass
    
    agent_chain = create_paradise_agent(llm, use_rag=use_rag, use_tools=use_tools, announcement_callback=announce_tool_usage)
    chat_history = []
    
    try:
        stt_plugin = openai.STT(
            model="whisper-1",
            language="en",
        )
        
        stt_engine = stt_plugin.stream()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
    
    try:
        tts_engine = openai.TTS()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
    
    agent_audio_source = rtc.AudioSource(tts_engine.sample_rate, tts_engine.num_channels)
    agent_audio_track = rtc.LocalAudioTrack.create_audio_track("agent-voice", agent_audio_source)
    await ctx.room.local_participant.publish_track(agent_audio_track)
    
    user_audio_track = None
    for track_publication in participant.track_publications.values():
        if track_publication.kind == rtc.TrackKind.KIND_AUDIO and track_publication.track:
            user_audio_track = track_publication.track
            break
    
    if not user_audio_track:
        async def wait_for_audio_track():
            nonlocal user_audio_track
            attempts = 0
            max_attempts = 100
            while not user_audio_track and attempts < max_attempts:
                await asyncio.sleep(0.1)
                attempts += 1
                for track_publication in participant.track_publications.values():
                    if track_publication.kind == rtc.TrackKind.KIND_AUDIO and track_publication.track:
                        user_audio_track = track_publication.track
                        return
        await wait_for_audio_track()
    
    if not user_audio_track:
        raise RuntimeError("No user audio track found")
    
    audio_stream = rtc.AudioStream(user_audio_track)
    
    async def send_transcript(room: rtc.Room, text: str, is_user: bool):
        """Send transcript to frontend via LiveKit data channel."""
        try:
            data = json.dumps({
                "type": "transcript",
                "text": text,
                "is_user": is_user,
            })
            await room.local_participant.publish_data(
                data.encode("utf-8"),
                topic="transcript",
            )
        except Exception as e:
            pass
    
    async def transcribe_audio():
        """Process audio and send transcripts to frontend."""
        frame_count = 0
        try:
            async for event in audio_stream:
                frame_count += 1
                
                if not hasattr(event, 'frame') or event.frame is None:
                    continue
                
                frame = event.frame
                
                stt_engine.push_frame(frame)
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    last_transcript = None
    last_transcript_time = 0
    is_processing = False
    is_speaking = False
    
    async def process_announcements():
        """Process announcements from queue and speak them immediately."""
        nonlocal is_speaking
        while True:
            try:
                announcement = await asyncio.wait_for(announcement_queue.get(), timeout=0.1)
                await send_transcript(ctx.room, announcement, is_user=False)
                await speak_text(announcement)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                continue
    
    async def handle_transcription():
        """Handle STT events, get LLM response, and speak it back."""
        nonlocal last_transcript, last_transcript_time, is_processing, is_speaking
        
        try:
            async for event in stt_engine:
                if isinstance(event, stt.SpeechEvent):
                    if event.alternatives and len(event.alternatives) > 0:
                        user_transcript = event.alternatives[0].text
                        if not user_transcript.strip():
                            continue
                        
                        current_time = time.time()
                        
                        if user_transcript == last_transcript and (current_time - last_transcript_time) < 2.0:
                            continue
                        
                        if is_processing or is_speaking:
                            continue
                        
                        if event.type != stt.SpeechEventType.FINAL_TRANSCRIPT:
                            continue
                        
                        is_processing = True
                        last_transcript = user_transcript
                        last_transcript_time = current_time
                        
                        await send_transcript(ctx.room, user_transcript, is_user=True)
                        
                        chat_history.append({"role": "user", "content": user_transcript})
                        
                        await asyncio.sleep(0.5)
                        
                        try:
                            agent_response = await get_agent_response(
                                agent_chain, 
                                user_transcript, 
                                chat_history[:-1],
                                use_rag=use_rag,
                                use_tools=use_tools
                            )
                            
                            await send_transcript(ctx.room, agent_response, is_user=False)
                            
                            chat_history.append({"role": "assistant", "content": agent_response})
                            
                            await speak_text(agent_response)
                            
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            error_msg = "I'm sorry, I encountered an error. Please try again."
                            await send_transcript(ctx.room, error_msg, is_user=False)
                        finally:
                            is_processing = False
        except Exception as e:
            import traceback
            traceback.print_exc()
            is_processing = False
            is_speaking = False
    
    async def speak_text(text: str):
        """Convert text to speech and stream to room."""
        nonlocal is_speaking
        is_speaking = True
        frame_count = 0
        
        try:
            async for output in tts_engine.synthesize(text):
                if hasattr(output, 'frame') and output.frame:
                    frame_count += 1
                    await agent_audio_source.capture_frame(output.frame)
                elif hasattr(output, 'audio') and output.audio:
                    frame_count += 1
                    if hasattr(output.audio, 'frame'):
                        await agent_audio_source.capture_frame(output.audio.frame)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                pass
            else:
                import traceback
                traceback.print_exc()
        finally:
            is_speaking = False
    
    greeting = "Hey! I'm Paradise, your travel planning buddy. What can I help you with today?"
    await send_transcript(ctx.room, greeting, is_user=False)
    await speak_text(greeting)
    
    cleanup_done = False
    
    async def cleanup_resources():
        """Clean up STT and TTS resources gracefully."""
        nonlocal cleanup_done
        if cleanup_done:
            return
        cleanup_done = True
        
        try:
            if 'stt_engine' in locals() and stt_engine:
                try:
                    if hasattr(stt_engine, 'end_input'):
                        stt_engine.end_input()
                    if hasattr(stt_engine, 'aclose'):
                        await stt_engine.aclose()
                except Exception as e:
                    pass
        except Exception as e:
            pass
    
    try:
        async def wait_for_disconnect():
            try:
                disconnected_state = 0
                while int(ctx.room.connection_state) != disconnected_state:
                    await asyncio.sleep(0.5)
            except Exception as e:
                pass
            finally:
                await cleanup_resources()
                try:
                    await ctx.shutdown(reason="User ended call")
                except Exception as e:
                    pass
        
        await asyncio.gather(
            transcribe_audio(),
            handle_transcription(),
            process_announcements(),
            wait_for_disconnect(),
        )
    except asyncio.CancelledError:
        await cleanup_resources()
    except Exception as e:
        import traceback
        traceback.print_exc()
        await cleanup_resources()
    finally:
        pass
