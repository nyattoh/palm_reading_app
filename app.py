from flask import Flask, request, render_template, redirect, url_for, jsonify, send_file
import os
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import json
import uuid

# Flaskアプリケーションの設定
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SHARE_FOLDER'] = 'shared/'

# アップロードされた画像の許可された拡張子
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# トップページ
@app.route('/')
def index():
    return render_template('index.html')

# 画像アップロード処理
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # 画像処理を行う関数を呼び出し
        result, annotated_image_path = analyze_palm(filepath)
        share_id = str(uuid.uuid4())
        shared_filepath = os.path.join(app.config['SHARE_FOLDER'], f'{share_id}.json')
        with open(shared_filepath, 'w', encoding='utf-8') as f:
            f.write(result)
        return render_template('result.html', result=json.loads(result), annotated_image=annotated_image_path, share_link=url_for('share', share_id=share_id, _external=True))
    return redirect(url_for('index'))

# 共有リンクで結果を表示
@app.route('/share/<share_id>', methods=['GET'])
def share(share_id):
    shared_filepath = os.path.join(app.config['SHARE_FOLDER'], f'{share_id}.json')
    if not os.path.exists(shared_filepath):
        return "共有された結果が見つかりません。", 404
    with open(shared_filepath, 'r', encoding='utf-8') as f:
        result = json.load(f)
    return render_template('shared_result.html', result=result)

# 手のひらの画像を解析する関数
def analyze_palm(image_path):
    # OpenCVで画像を読み込み
    img = cv2.imread(image_path)
    if img is None:
        return "画像の読み込みに失敗しました。", None
    
    # ここで画像処理や手相のライン検出を行う
    detected_lines = detect_lines(img)
    detected_marks = detect_marks_and_mounds(img)
    
    # 手相の5つの視点からの解析結果を取得
    indian_result = analyze_indian_palmistry(detected_lines)
    western_result = analyze_western_palmistry(detected_lines)
    japanese_result = analyze_japanese_palmistry(detected_lines)
    fortune_result = analyze_financial_palmistry(detected_lines)
    love_result = analyze_love_palmistry(detected_lines)
    relationship_result = analyze_relationship_palmistry(detected_lines)
    
    # 解釈を統合し、良い判断を優先
    consolidated_result = consolidate_results([indian_result, western_result, japanese_result, fortune_result, love_result, relationship_result])

    # 線と印の描画結果を保存
    annotated_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'annotated_palm.png')
    cv2.imwrite(annotated_image_path, img)
    
    return consolidated_result, 'uploads/annotated_palm.png'

# 線を検出して描画する関数
def detect_lines(image):
    # 画像の前処理（グレースケール変換、ぼかし、エッジ検出など）
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # ライン検出（Hough変換を使用）
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=50, maxLineGap=10)
    
    # 検出されたラインを画像に色分けして描画
    if lines is not None:
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
        for idx, line in enumerate(lines):
            for x1, y1, x2, y2 in line:
                color = colors[idx % len(colors)]
                cv2.line(image, (x1, y1), (x2, y2), color, 2)
    return lines

# 丘や印を検出する関数
def detect_marks_and_mounds(image):
    # 仮の実装：将来的に特定のパターン認識を追加する
    # ここで丘や印（スター、クロス、トライアングルなど）を検出して解析を行う
    return []

# 各地域の手相学の解釈を統合する関数
def consolidate_results(results):
    consolidated = {}
    for result in results:
        for line, interpretation in json.loads(result).items():
            if line not in consolidated or "悪い判断" in consolidated[line]:
                consolidated[line] = interpretation
    return json.dumps(consolidated, ensure_ascii=False, indent=2)

# インド手相学に基づく解析
def analyze_indian_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "線が検出されませんでした。"}, ensure_ascii=False)
    # ラインごとにインド手相学の特徴を適用
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            # 線の長さや角度に基づいて解釈を追加
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if length > 100:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "長い生命線: 健康と長寿を示唆します。"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "短い生命線: 健康面に注意が必要です。"
    return json.dumps(analysis, ensure_ascii=False)

# 西洋手相学に基づく解析
def analyze_western_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "線が検出されませんでした。"}, ensure_ascii=False)
    # ラインの形状や位置から西洋手相学的に解釈
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if y1 < y2:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "感情線: 感情が豊かで安定していることを示します。"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "感情線: 感情の波が激しい可能性があります。"
    return json.dumps(analysis, ensure_ascii=False)

# 日本手相学に基づく解析
def analyze_japanese_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "線が検出されませんでした。"}, ensure_ascii=False)
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            if x1 < image.shape[1] // 2:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "家庭運に関する線: 家族関係が重要です。"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "仕事運に関する線: 仕事における成功を示唆します。"
    return json.dumps(analysis, ensure_ascii=False)

# 財運に基づく解析
def analyze_financial_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "線が検出されませんでした。"}, ensure_ascii=False)
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if length > 150 and y1 > image.shape[0] // 2:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "財運線: 経済的な安定と成功を示唆します。"
            elif length > 100:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "中程度の財運線: 財政的な成長の可能性がありますが、注意が必要です。"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "短い財運線: 財政的なリスクや困難が予測されます。"
    return json.dumps(analysis, ensure_ascii=False)

# 恋愛や出会いに関する解析
def analyze_love_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "線が検出されませんでした。"}, ensure_ascii=False)
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if y1 < image.shape[0] // 3:
                if length > 100:
                    analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "長い感情線: 深い愛情と安定した関係を示唆します。"
                else:
                    analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "短い感情線: 恋愛における注意が必要です。"
            elif y1 >= image.shape[0] // 3 and y1 < image.shape[0] * 2 // 3:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "結婚線: 出会いや結婚に関する重要な兆候を示しています。"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "愛情線: 強い恋愛運を示唆します。"
    return json.dumps(analysis, ensure_ascii=False)

# 人間関係に関する解析
def analyze_relationship_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "線が検出されませんでした。"}, ensure_ascii=False)
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if y1 > image.shape[0] // 2 and length > 100:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "友情線: 深い友情や信頼できる人間関係を築く力を示唆します。"
            elif y1 < image.shape[0] // 2 and length > 50:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "人間関係の線: 他者との強い繋がりを持つ傾向があります。"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "人間関係の線: 調整が必要です。"
    return json.dumps(analysis, ensure_ascii=False)

if __name__ == '__main__':
    # アップロードフォルダの作成
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['SHARE_FOLDER']):
        os.makedirs(app.config['SHARE_FOLDER'])
    
    # アプリケーションの実行
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
