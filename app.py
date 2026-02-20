from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile

app = Flask(__name__)
CORS(app)

COOKIE_FILE = "/etc/secrets/cookies.txt"


@app.route('/')
def health():
    return "OK", 200


@app.route('/info')
def info():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    ydl_opts = {
        'quiet': True,
        'cookiefile': COOKIE_FILE
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(url, download=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    duration_seconds = data.get('duration', 0)
    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)

    return jsonify({
        'title': data.get('title'),
        'thumbnail': data.get('thumbnail'),
        'duration': f"{minutes}:{str(seconds).zfill(2)}",
        'channel': data.get('uploader'),
        'views': f"{data.get('view_count', 0):,} views",
    })


@app.route('/download', methods=['POST'])
def download():
    body = request.json
    if not body:
        return jsonify({'error': 'Missing JSON body'}), 400

    url = body.get('url')
    fmt = body.get('format')
    quality = body.get('quality')

    if not url or not fmt:
        return jsonify({'error': 'Missing required fields'}), 400

    tmp = tempfile.mkdtemp()

    ydl_opts = {
        'format': 'bestaudio/best' if fmt == 'mp3'
                  else f'bestvideo[height<={quality[:-1]}]+bestaudio/best',
        'outtmpl': os.path.join(tmp, '%(title)s.%(ext)s'),
        'postprocessors': (
            [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
            if fmt == 'mp3' else []
        ),
        'quiet': True,
        'cookies':COOKIE_FILE
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    file_name = next(os.path.join(tmp, f) for f in os.listdir(tmp))
    return send_file(file_name, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
