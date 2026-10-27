#!/bin/sh
# House render pipeline (one lossy encode): 2x supersampled lossless PNG capture (3840x2160) plus the audio
# mix, lanczos downscale to 1920x1080, H.264 High CRF 14 preset slow yuv420p 30 fps, AAC 192k, faststart;
# no -tune, no sharpening. The poster is a frame of the same 4K sequence (never upscaled, never decoded
# from the mp4). Run from .assets/demo/project.  Usage: sh tools/render.sh [work_dir]
set -e
REPO=claim-assistant
POSTER_T=3.8
# a key frame at the end card start, so no I-frame lands inside its still hold (a visible quantisation step)
END_CARD=$(sed -n 's/.*id="outro"[^>]*data-start="\([0-9.]*\)".*/\1/p' index.html | head -1)
DUR=$(sed -n 's/.*data-composition-id="main"[^>]*data-duration="\([0-9.]*\)".*/\1/p' index.html | head -1)
FRAMES=$(python3 -c "print(round($DUR*30))")
TMP=${1:-$(mktemp -d)}

npx hyperframes render --format png-sequence --resolution landscape-4k --fps 30 --output "$TMP/frames"
FIRST=$(ls "$TMP/frames" | grep -m1 '^frame_')
START=$(echo "$FIRST" | sed 's/frame_0*\([0-9]*\)\.png/\1/'); START=${START:-0}

ffmpeg -y -framerate 30 -start_number "$START" -i "$TMP/frames/frame_%06d.png" -i "$TMP/frames/audio.m4a" \
  -map 0:v -map 1:a -frames:v "$FRAMES" \
  -vf "scale=1920:1080:flags=lanczos+accurate_rnd+full_chroma_int:out_color_matrix=bt709:out_range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 14 -profile:v high -pix_fmt yuv420p -r 30 \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -force_key_frames "$END_CARD" -movflags +faststart -t "$DUR" "../demo-$REPO.mp4"

N=$(python3 -c "print(round($POSTER_T*30) + $START)")
ffmpeg -y -i "$TMP/frames/frame_$(printf %06d "$N").png" -vf format=rgb24 ../poster.png
file ../poster.png
echo "frames kept in $TMP/frames"
