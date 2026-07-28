curl -X POST http://localhost:5001/process-tennis-video \
  -F "video=@test_videos/video1.mp4" \
  -o response.json \
  -D headers.txt \
  -v