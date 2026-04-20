# YT-Sub-n-Dub
Tool that uses OpenAI's Whisper, Qwen3-TTS, yt-dlp, and FFMPEG to create subtitles and english dubbing for downloaded YouTube videos.

I only really put this together because there's a load of Japanese, Korean, and Chinese art tutorials on YouTube and BiliBili that I would like to learn from. The problem is that YouTube's translation features suck even compared to Google Translate, their AI dubbing is garbage, and BiliBili has neither of those things. I still need to add support for the cookies parameter of yt-dlp (So BiliBili can be used), and maybe put together a simple GUI for people who don't want to dick with the terminal too much.

### Usage Instructions (NixOS):
1. Make sure that ffmpeg-full, whisper-cpp, python, and yt-dlp are installed.
2. Run ``setup.sh`` to download the necessary whisper model. (This only needs to be done once).
3. Run ``subndub.sh``.

I have not tested this outside of NixOS, and this isn't using a nix-develop shell at the moment (outside of Qwen3-TTS WebUI), so feel free to contribute changes if you want.