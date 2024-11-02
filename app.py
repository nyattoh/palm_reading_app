from flask import Flask, request, render_template, redirect, url_for, jsonify, send_file
import os
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import json
import uuid

# Flask�A�v���P�[�V�����̐ݒ�
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SHARE_FOLDER'] = 'shared/'

# �A�b�v���[�h���ꂽ�摜�̋����ꂽ�g���q
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# �g�b�v�y�[�W
@app.route('/')
def index():
    return render_template('index.html')

# �摜�A�b�v���[�h����
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
        # �摜�������s���֐����Ăяo��
        result, annotated_image_path = analyze_palm(filepath)
        share_id = str(uuid.uuid4())
        shared_filepath = os.path.join(app.config['SHARE_FOLDER'], f'{share_id}.json')
        with open(shared_filepath, 'w', encoding='utf-8') as f:
            f.write(result)
        return render_template('result.html', result=json.loads(result), annotated_image=annotated_image_path, share_link=url_for('share', share_id=share_id, _external=True))
    return redirect(url_for('index'))

# ���L�����N�Ō��ʂ�\��
@app.route('/share/<share_id>', methods=['GET'])
def share(share_id):
    shared_filepath = os.path.join(app.config['SHARE_FOLDER'], f'{share_id}.json')
    if not os.path.exists(shared_filepath):
        return "���L���ꂽ���ʂ�������܂���B", 404
    with open(shared_filepath, 'r', encoding='utf-8') as f:
        result = json.load(f)
    return render_template('shared_result.html', result=result)

# ��̂Ђ�̉摜����͂���֐�
def analyze_palm(image_path):
    # OpenCV�ŉ摜��ǂݍ���
    img = cv2.imread(image_path)
    if img is None:
        return "�摜�̓ǂݍ��݂Ɏ��s���܂����B", None
    
    # �����ŉ摜������葊�̃��C�����o���s��
    detected_lines = detect_lines(img)
    detected_marks = detect_marks_and_mounds(img)
    
    # �葊��5�̎��_����̉�͌��ʂ��擾
    indian_result = analyze_indian_palmistry(detected_lines)
    western_result = analyze_western_palmistry(detected_lines)
    japanese_result = analyze_japanese_palmistry(detected_lines)
    fortune_result = analyze_financial_palmistry(detected_lines)
    love_result = analyze_love_palmistry(detected_lines)
    relationship_result = analyze_relationship_palmistry(detected_lines)
    
    # ���߂𓝍����A�ǂ����f��D��
    consolidated_result = consolidate_results([indian_result, western_result, japanese_result, fortune_result, love_result, relationship_result])

    # ���ƈ�̕`�挋�ʂ�ۑ�
    annotated_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'annotated_palm.png')
    cv2.imwrite(annotated_image_path, img)
    
    return consolidated_result, 'uploads/annotated_palm.png'

# �������o���ĕ`�悷��֐�
def detect_lines(image):
    # �摜�̑O�����i�O���[�X�P�[���ϊ��A�ڂ����A�G�b�W���o�Ȃǁj
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # ���C�����o�iHough�ϊ����g�p�j
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=50, maxLineGap=10)
    
    # ���o���ꂽ���C�����摜�ɐF�������ĕ`��
    if lines is not None:
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
        for idx, line in enumerate(lines):
            for x1, y1, x2, y2 in line:
                color = colors[idx % len(colors)]
                cv2.line(image, (x1, y1), (x2, y2), color, 2)
    return lines

# �u�������o����֐�
def detect_marks_and_mounds(image):
    # ���̎����F�����I�ɓ���̃p�^�[���F����ǉ�����
    # �����ŋu���i�X�^�[�A�N���X�A�g���C�A���O���Ȃǁj�����o���ĉ�͂��s��
    return []

# �e�n��̎葊�w�̉��߂𓝍�����֐�
def consolidate_results(results):
    consolidated = {}
    for result in results:
        for line, interpretation in json.loads(result).items():
            if line not in consolidated or "�������f" in consolidated[line]:
                consolidated[line] = interpretation
    return json.dumps(consolidated, ensure_ascii=False, indent=2)

# �C���h�葊�w�Ɋ�Â����
def analyze_indian_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "�������o����܂���ł����B"}, ensure_ascii=False)
    # ���C�����ƂɃC���h�葊�w�̓�����K�p
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            # ���̒�����p�x�Ɋ�Â��ĉ��߂�ǉ�
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if length > 100:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "����������: ���N�ƒ������������܂��B"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�Z��������: ���N�ʂɒ��ӂ��K�v�ł��B"
    return json.dumps(analysis, ensure_ascii=False)

# ���m�葊�w�Ɋ�Â����
def analyze_western_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "�������o����܂���ł����B"}, ensure_ascii=False)
    # ���C���̌`���ʒu���琼�m�葊�w�I�ɉ���
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if y1 < y2:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�����: ����L���ň��肵�Ă��邱�Ƃ������܂��B"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�����: ����̔g���������\��������܂��B"
    return json.dumps(analysis, ensure_ascii=False)

# ���{�葊�w�Ɋ�Â����
def analyze_japanese_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "�������o����܂���ł����B"}, ensure_ascii=False)
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            if x1 < image.shape[1] // 2:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�ƒ�^�Ɋւ����: �Ƒ��֌W���d�v�ł��B"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�d���^�Ɋւ����: �d���ɂ����鐬�����������܂��B"
    return json.dumps(analysis, ensure_ascii=False)

# ���^�Ɋ�Â����
def analyze_financial_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "�������o����܂���ł����B"}, ensure_ascii=False)
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if length > 150 and y1 > image.shape[0] // 2:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "���^��: �o�ϓI�Ȉ���Ɛ������������܂��B"
            elif length > 100:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�����x�̍��^��: �����I�Ȑ����̉\��������܂����A���ӂ��K�v�ł��B"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�Z�����^��: �����I�ȃ��X�N�⍢��\������܂��B"
    return json.dumps(analysis, ensure_ascii=False)

# ������o��Ɋւ�����
def analyze_love_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "�������o����܂���ł����B"}, ensure_ascii=False)
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if y1 < image.shape[0] // 3:
                if length > 100:
                    analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "���������: �[������ƈ��肵���֌W���������܂��B"
                else:
                    analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�Z�������: �����ɂ����钍�ӂ��K�v�ł��B"
            elif y1 >= image.shape[0] // 3 and y1 < image.shape[0] * 2 // 3:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "������: �o��⌋���Ɋւ���d�v�Ȓ���������Ă��܂��B"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�����: ���������^���������܂��B"
    return json.dumps(analysis, ensure_ascii=False)

# �l�Ԋ֌W�Ɋւ�����
def analyze_relationship_palmistry(lines):
    if lines is None:
        return json.dumps({"message": "�������o����܂���ł����B"}, ensure_ascii=False)
    analysis = {}
    for line in lines:
        for x1, y1, x2, y2 in line:
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if y1 > image.shape[0] // 2 and length > 100:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�F���: �[���F���M���ł���l�Ԋ֌W��z���͂��������܂��B"
            elif y1 < image.shape[0] // 2 and length > 50:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�l�Ԋ֌W�̐�: ���҂Ƃ̋����q��������X��������܂��B"
            else:
                analysis[f"line_{x1}_{y1}_{x2}_{y2}"] = "�l�Ԋ֌W�̐�: �������K�v�ł��B"
    return json.dumps(analysis, ensure_ascii=False)

if __name__ == '__main__':
    # �A�b�v���[�h�t�H���_�̍쐬
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['SHARE_FOLDER']):
        os.makedirs(app.config['SHARE_FOLDER'])
    
    # �A�v���P�[�V�����̎��s
	app.run(host='0.0.0.0', port=10000)
	