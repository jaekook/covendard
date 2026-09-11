# Covendard specimens

두 PNG는 실제 WOFF2를 Chromium에 로드하여 2배 해상도로 캡처했다.
HTML/CSS 원본은 `specimens.html`, 렌더러는 `../../scripts/render_specimens.cjs`다.
AI 생성 이미지나 실제 에디터·터미널 캡처가 아니다.

- `code.png`: 코드 본문 24 CSS px, 행간 1.8, Regular·Bold·Italic, ligatures on.
- `spacing.png`: 동일 문장, Regular 30 CSS px, 행간 1.8, letter-spacing 0.
  기준 폰트는 기존 Jetendard Cove Regular(균등 1.15), 비교 폰트는 Covendard
  Regular(가로 1.20·세로 1.15). 양쪽 영문 소스와 한글 advance는 같다.
- Chromium에서 양쪽 첫 문장 advance가 모두 510 CSS px임을 검사했다.
- PNG 가로는 2200px이며 README 표시 크기에 맞춰 축소된다. 실제 눈에 보이는
  차이는 운영체제·렌더러·크기·디스플레이에 따라 달라질 수 있다.

## 재현

프로젝트 루트에서 실행한다. Playwright는 폰트 빌드의 런타임 의존성에 추가하지 않는다.

```sh
make run
# 원본과 같은 배율로 비교용 글리프를 생성한다. 패밀리 이름만 다르다.
uv run covendard --variants Regular --korean-scale 1.15 \
  --family-name "Cove Baseline" --output-dir fonts/specimens/baseline

npm install --prefix /tmp/covendard-specimens playwright@1.63.0
/tmp/covendard-specimens/node_modules/.bin/playwright install chromium
NODE_PATH=/tmp/covendard-specimens/node_modules node scripts/render_specimens.cjs \
  fonts/specimens/baseline/webfont/CoveBaseline-Regular.woff2
```

최초 이미지 생성에는 기존 `../jetendard/fonts/webfont/JetendardCove-Regular.woff2`를
비교 입력으로 사용했다. 폰트 원본은 저장소에 추가하지 않았다.
