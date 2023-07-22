# -*- coding: utf-8 -*-
# какать пользоваться: открыть командную обочку Windows (Win+R -> cmd -> Enter), перетянуть в ее окно этот файл, поставить пробел, перетянуть в окно cmd папку с изображениями
# откроется браузер с вебинтерфейсом (если не открылся, то открыть самостоятельно адрес который будет написан в выоде)
# под каждым изображением нужно будет ввести описание, когда все будет сделано - нажать в нижнем правом углу кнопку для перевода описаний
# все описания сохраняются в одноименные изображениям текстовые файлы, буквально при каждом вводе символа

import os, argparse, webbrowser, socketserver, json, subprocess, re, threading
from xml.sax.saxutils import escape
import http.server
from http.server import BaseHTTPRequestHandler, HTTPServer
try: from yandexfreetranslate import YandexFreeTranslate
except: subprocess.run(["pip", "install", "yandexfreetranslate"])

def create_index_html(image_folder):
    image_files = [file for file in os.listdir(image_folder) if file.endswith(('.jpg', '.jpeg', '.png'))]
    with open(os.path.join(image_folder, 'index.html'), 'w', encoding='utf-8', newline='\n') as index_file:
        index_file.write('''<!doctype html>\n<html lang="ru">\n<html>\n<head>\n<meta charset="utf-8" />\n<title>разметка картинок</title>\n
<script>
window.addEventListener('DOMContentLoaded', (event) => {
  const textareas = document.querySelectorAll('textarea');
  textareas.forEach((textarea) => {
    const filename = textarea.id;
    fetch(`http://localhost:8000/${filename}.txt`)
      .then(response => response.text())
      .then(data => {
        textarea.value = data;
      })
      .catch(error => console.log(error));
  });
  textareas.forEach((textarea) => {
    textarea.addEventListener('input', (event) => {
      const filename = event.target.id;
      const text = event.target.value;
      fetch(`http://localhost:8000/${filename}.txt`, {
        method: 'POST',
        body: text
      })
        .then(response => console.log(response))
        .catch(error => console.log(error));
    });
  });
});
</script>
<style>
html,
body {
	background: #191919;
	color: #ebebeb;
	margin: 0;
	padding: 0;
}
containter {
	display: flex;
	flex-direction: row;
	flex-wrap: wrap;
	justify-content: flex-start;
	align-items: center;
}
.image_and_caption {
	position: relative;
	height: 512px;
	width: 512px;
	display: flex0;
	flex-direction: column;
	align-items: center;
	opacity: 0;
	transition: opacity 0.5s;
	margin: 20px 10px 0px 0px;
	margin-left: 10px;
	padding: 10px 10px 130px 10px;
	border: 4px solid #242424;
}
.image_and_caption img {
	padding: 0;
	margin: 0;
	height: 512px;
	display: block;
}
.image_and_caption textarea {
	position: absolute;
	z-index: 10;
	height: 120px!important;
	width: 512px;
	border: none;
	resize: none;
	padding: 15px;
	box-sizing: border-box;
	background: #0000004f;
	color: #9ec29f;
}
#TranslateButton {
	height: 40px;
	color: #fff;
	background-color: #292826;
	background-image: url(https://translate.yandex.ru/icons/favicon.png);
	background-repeat: no-repeat;
	background-size: 30px;
	background-position-y: center;
	background-position-x: 4px;
	padding: 0 10px 0px 40px;
	border-radius: 30px;
	border: unset;
	cursor: pointer;
	filter: drop-shadow(0 0 10px #000);
	transition: 0.5s;
	position: fixed;
	bottom: 20px;
	right: 20px;
}
#TranslateButton:hover {
	background-color: #000;
	filter: drop-shadow(0 0 10px #c6b18a4a);
}
#TranslateButton:active {
	color: #000;
	background-color: #878787;
	filter: drop-shadow(0 0 10px #000);
}
.image_and_caption {
  opacity: 0;
  transition: 0.5s ease-in;
}
overlay {
	position: fixed;
	width: 100vw;
	height: 2100vw;
	background: #000;
	margin: 0;
	padding: 0;
	z-index: 99;
}
#translate_progress{
	z-index: 999;
	position: fixed;
	width: 100vw;
	height: fit-content;
	margin: 0;
	padding: 0;
	filter: url(#threshold) blur(0.6px);
}
/* cyrillic */
@font-face {
  font-family: 'Bad Script';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(https://fonts.gstatic.com/s/badscript/v16/6NUT8F6PJgbFWQn47_x7pO8kzO1A.woff2) format('woff2');
  unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
}
/* latin */
@font-face {
  font-family: 'Bad Script';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(https://fonts.gstatic.com/s/badscript/v16/6NUT8F6PJgbFWQn47_x7pOskzA.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
#text1, #text2 {
	position: absolute;
	width: 100vw;
	display: block;
	font-size: 80pt;
	text-align: center;
	user-select: none;
	top: 15vw;
	--textcolor:#1553d7;
}
#text1 {
	color: var(--textcolor);
	font-family: 'Bad Script';
}
#text2 {
	color: var(--textcolor);
	font-family: 'Bad Script';
}
#filters {
	width: 0;
	height: 0;
	display: none;
}
.translation_inprogress {
	font-family: sans-serif;
	position: relative;
	top: 100px;
	text-align: center;
	font-size: 1.2em;
}
.translation_inprogress span {
	position: relative;
	display: block;
	top: 1em;
	font-size: 0.7em;
	color: #3c3c3c;
}
.translation_inprogress_bottom {
	font-family: sans-serif;
	position: relative;
	bottom: -850px;
	text-align: center;
	font-size: 1.2em;
	display: flex;
	flex-direction: column;
	flex-wrap: wrap;
	align-content: center;
	justify-content: center;
	align-items: center;
}
.loader {
	width: 70%;
	height: 4.8px;
	display: inline-block;
	background: rgba(255, 255, 255, 0.15);
	position: relative;
	top: -2em;
	overflow: hidden;
}
.loader::after {
	content: '';
	width: 0%;
	height: 4.8px;
	background-color: #3e3e3e;
	background-image: linear-gradient(45deg, rgba(0, 0, 0, .25) 25%, transparent 25%, transparent 50%, rgba(0, 0, 0, 0.25) 50%, rgba(0, 0, 0, 0.25) 75%, transparent 75%, transparent);
	background-size: 15px 15px;
	position: absolute;
	top: 0;
	left: 0;
	box-sizing: border-box;
	animation: animFw 6s ease-in infinite;
}
@keyframes animFw {
	0% {
		width: 0;
	}
	100% {
		width: 100%;
	}
}
</style>
</head>\n
<body>\n<overlay style="display:none;"><div class="translation_inprogress">выполняется перевод с русского на английский...<span>работоспособность перевода не гарантируется, т.к. зависит от доступности серверов яндекса с данного ip, а так же от того насколько сетевой запрос покажется подозрительным яндексу.</span></div><div id="translate_progress">
<svg id="filters"><defs><filter id="threshold">
<feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0
0 1 0 0 0
0 0 1 0 0
0 0 0 255 -140" /></filter></defs></svg>
<span id="text1"></span>
<span id="text2"></span>
</div><div class="translation_inprogress_bottom"><span class="loader"></span>после завершения перевода страница обновится</div></overlay>\n<containter>''')
        for image_file in image_files:
            image_tag = f'<img src="{escape(image_file)}"/>'
            textarea_tag = f'<textarea id="{escape(os.path.splitext(image_file)[0])}"></textarea>'
            div_tag = f'<div class="image_and_caption">\n\t{image_tag}\n\t{textarea_tag}\n</div>'
            index_file.write(div_tag + '\n')
        index_file.write('''</container>\n<button id="TranslateButton" type="button">перевести все промпты на английский</button>\n<script>
function lazyLoad() {
  const elements = document.querySelectorAll('.image_and_caption');
  elements.forEach(element => {
	const rect = element.getBoundingClientRect();
	if (rect.top < window.innerHeight) {
	  const img = element.querySelector('img');
	  element.style.opacity = 1;
	}
  });
}

window.addEventListener('scroll', lazyLoad);
window.addEventListener('resize', lazyLoad);
lazyLoad();
const trbutton = document.querySelector('#TranslateButton');
trbutton.addEventListener('click', (event) => {
  document.querySelector("body > overlay").removeAttribute("style");
  fetch('http://localhost:8000/translate', {
    method: 'POST'
  })
    .then(response => {
      if (response.ok) {
        location.reload();
      }
    })
    .catch(error => console.log(error));
});
const elts = {
	text1: document.getElementById("text1"),
	text2: document.getElementById("text2")
};
const texts = ["пролапс", "prolapse", "хуй", "dick", "мошонка", "scrotum", "елдак", "prick", "пидорас", "faggot", "прямая кишка", "rectum", "залупа", "dickhead"];
const morphTime = 1.3;
const cooldownTime = 0.5;
let textIndex = texts.length - 1;
let time = new Date();
let morph = 0;
let cooldown = cooldownTime;
elts.text1.textContent = texts[textIndex % texts.length];
elts.text2.textContent = texts[(textIndex + 1) % texts.length];
function doMorph() {
	morph -= cooldown;
	cooldown = 0;
	let fraction = morph / morphTime;
	if (fraction > 1) {
		cooldown = cooldownTime;
		fraction = 1;
	}
	setMorph(fraction);
}
function setMorph(fraction) {
	elts.text2.style.filter = `blur(${Math.min(8 / fraction - 8, 100)}px)`;
	elts.text2.style.opacity = `${Math.pow(fraction, 0.4) * 100}%`;
	fraction = 1 - fraction;
	elts.text1.style.filter = `blur(${Math.min(8 / fraction - 8, 100)}px)`;
	elts.text1.style.opacity = `${Math.pow(fraction, 0.4) * 100}%`;
	elts.text1.textContent = texts[textIndex % texts.length];
	elts.text2.textContent = texts[(textIndex + 1) % texts.length];
}
function doCooldown() {
	morph = 0;
	elts.text2.style.filter = "";
	elts.text2.style.opacity = "100%";
	elts.text1.style.filter = "";
	elts.text1.style.opacity = "0%";
}
function animate() {
	requestAnimationFrame(animate);
	let newTime = new Date();
	let shouldIncrementIndex = cooldown > 0;
	let dt = (newTime - time) / 1000;
	time = newTime;
	cooldown -= dt;
	if (cooldown <= 0) {
		if (shouldIncrementIndex) {
			textIndex++;
		}
		doMorph();
	} else {
		doCooldown();
	}
}
animate();
</script>\n</body>\n</html>''')

def create_text_files(image_folder):
    image_files = [file for file in os.listdir(image_folder) if file.endswith(('.jpg', '.jpeg', '.jiff', '.png', '.webp', '.avif', '.gif'))]
    for image_file in image_files:
        text_file_name = os.path.splitext(image_file)[0] + '.txt'
        text_file_path = os.path.join(image_folder, text_file_name)
        if not os.path.exists(text_file_path):
            with open(text_file_path, 'w') as text_file:
                text_file.write(image_file)
            
class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        filename = self.path[1:]
        if self.path != '/translate':
            with open(filename, 'w', encoding='utf-8', newline='\n') as file:
                file.write(post_data.decode("utf-8"))
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/translate':
            translate(args.image_folder)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Success')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def get_local_ip():
    try:
        output = subprocess.check_output("ipconfig", shell=True).decode("cp866")
        pattern = r"Адаптер Ethernet.*?IPv4-адрес.*?: (.*?)\r\n.*?Маска подсети.*?: (.*?)\r\n"
        matches = re.findall(pattern, output, re.DOTALL)

        if matches:
            ip_address = matches[0][0]
            return ip_address
    except subprocess.CalledProcessError as e:
        None
    return None
def translate(image_folder):
    file_list = [file for file in os.listdir(image_folder) if file.endswith('.txt')]
    for file_name in file_list:
        file_path = os.path.join(image_folder, file_name)
        with open(file_path, 'r+', encoding='utf-8') as file:
            text = file.read()
            translated_text = YandexFreeTranslate(api="ios").translate("ru", "en", text)
            file.seek(0)
            file.write(translated_text)
            file.truncate()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Создание index.html на основе изображений в указанной папке')
    parser.add_argument('image_folder', help='Путь до папки с изображениями')
    args = parser.parse_args()
    os.chdir(args.image_folder)
    create_index_html(args.image_folder)
    create_text_files(args.image_folder)
    try:
        port = 8000
        server = HTTPServer(("", port), RequestHandler)
        print(f"сервер запущен на: http://127.0.0.1:{port}")
        local_ip = get_local_ip()
        ip_out = "адрес ПК (можно открыть на другом устройстве в этой сети): http://"+local_ip+":"+str(port)
        if local_ip:
            print(ip_out)
        else:
            print(f"или можно открыть на другом устройстве в этой сети http://ip_ПК_в_локальной_сети:{str(port)}")
        webbrowser.open_new_tab(f"http://localhost:{port}")
        print("а чтобы завершить - нужно тут нажать Ctl+C на клавиатуре")
        server.RequestHandlerClass.log_message = lambda *args: None
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        os.remove(os.path.join(args.image_folder, 'index.html'))
        print("работа завершена")
