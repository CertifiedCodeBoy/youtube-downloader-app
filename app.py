
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp, io, os, tempfile

app = Flask(__name__)
CORS(app)

@app.route('/info')
def info():
    url = request.args.get('url')
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        data = ydl.extract_info(url, download=False)
    return jsonify({
        'title': data.get('title'),
        'thumbnail': data.get('thumbnail'),
        'duration': str(int(data.get('duration', 0) // 60)) + ':' + str(data.get('duration', 0) % 60).zfill(2),
        'channel': data.get('uploader'),
        'views': f"{data.get('view_count', 0):,} views",
    })

@app.route('/download', methods=['POST'])
def download():
    body = request.json
    url, fmt, quality = body['url'], body['format'], body['quality']
    tmp = tempfile.mkdtemp()
    opts = {
        'format': 'bestaudio/best' if fmt == 'mp3' else f'bestvideo[height<={quality[:-1]}]+bestaudio/best',
        'outtmpl': os.path.join(tmp, '%(title)s.%(ext)s'),
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if fmt == 'mp3' else [],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    file = next(f for f in os.listdir(tmp))
    return send_file(os.path.join(tmp, file), as_attachment=True)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
