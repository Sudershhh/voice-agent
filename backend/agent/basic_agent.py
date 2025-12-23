"""Basic LiveKit agent that can join a room and handle connections."""

import asyncio
import json
import logging
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
from config import config

logger = logging.getLogger(__name__)


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
    
    use_rag = config.is_rag_enabled()
    
    use_tools = config.are_tools_enabled()
    
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
        
        room_state = ctx.room.connection_state
        room_state_int = int(room_state)
        if room_state_int == 0:
            logger.warning(
                "Audio: Room disconnected, skipping output",
                extra={
                    "room_state": str(room_state),
                    "room_state_int": room_state_int,
                    "text_length": len(text),
                }
            )
            is_speaking = False
            return
        
        audio_track_published = False
        for publication in ctx.room.local_participant.track_publications.values():
            if publication.track and publication.track.name == "agent-voice":
                audio_track_published = True
                break
        
        if not audio_track_published:
            logger.warning(
                "Audio: Track not published, skipping output",
                extra={"text_length": len(text)}
            )
            is_speaking = False
            return
        
        try:
            async for output in tts_engine.synthesize(text):
                current_state = int(ctx.room.connection_state)
                if current_state == 0:
                    logger.debug(
                        "Audio: Room disconnected during synthesis",
                        extra={
                            "room_state": str(ctx.room.connection_state),
                            "room_state_int": current_state,
                            "frames_sent": frame_count,
                        }
                    )
                    break
                
                try:
                    if hasattr(output, 'frame') and output.frame:
                        frame_count += 1
                        await agent_audio_source.capture_frame(output.frame)
                    elif hasattr(output, 'audio') and output.audio:
                        frame_count += 1
                        if hasattr(output.audio, 'frame'):
                            await agent_audio_source.capture_frame(output.audio.frame)
                except rtc.RtcError as rtc_error:
                    error_msg = str(rtc_error)
                    if "InvalidState" in error_msg or "invalid state" in error_msg.lower():
                        logger.warning(
                            "Audio: Capture failed (InvalidState)",
                            extra={
                                "error": str(rtc_error),
                                "room_state": str(ctx.room.connection_state),
                                "frames_sent": frame_count,
                            }
                        )
                        break
                    else:
                        logger.error(
                            "Audio: RTC error during capture",
                            extra={
                                "error": str(rtc_error),
                                "error_type": type(rtc_error).__name__,
                                "frames_sent": frame_count,
                            }
                        )
                        raise
                except Exception as frame_error:
                    logger.warning(
                        "Audio: Frame capture error",
                        extra={
                            "error": str(frame_error),
                            "error_type": type(frame_error).__name__,
                            "frames_sent": frame_count,
                        }
                    )
                    continue
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                logger.warning(
                    "Audio: TTS quota exceeded",
                    extra={
                        "error": error_msg,
                        "text_length": len(text),
                    }
                )
            else:
                logger.error(
                    "Audio: TTS synthesis error",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "text_length": len(text),
                    },
                    exc_info=True
                )
        finally:
            is_speaking = False
            if frame_count > 0:
                logger.debug(
                    "Audio: Output completed",
                    extra={
                        "frames_sent": frame_count,
                        "text_length": len(text),
                    }
                )
    
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
