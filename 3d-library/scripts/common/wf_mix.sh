#!/bin/bash
# usage: wf_mix.sh <dir> <duration>  -> mix.wav with voice padded to the full duration, mean about -22 dB
D=$1; DUR=$2
ffmpeg -v error -y -i $D/voice.mp3 -af "apad=whole_dur=$DUR" -ar 48000 $D/voice_pad.wav
mixit() { ffmpeg -v error -y -i $D/voice_pad.wav -i $D/music.wav -filter_complex "[1:a]volume=0.035[m];[m][0:a]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=300[md];[0:a][md]amix=inputs=2:normalize=0,volume=$1,alimiter=limit=0.93:level=false" -ar 48000 -t $DUR $D/mix.wav; }
mixit 2.0
m=$(ffmpeg -i $D/mix.wav -af volumedetect -f null - 2>&1 | grep mean_volume | awk '{print $5}')
g=$(python3 -c "print(round(2.0*10**((-22.0-($m))/20),3))")
mixit $g
ffmpeg -i $D/mix.wav -af volumedetect -f null - 2>&1 | grep -E "mean_vol|max_vol"
