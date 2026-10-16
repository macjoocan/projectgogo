# com.blgg.java800.com.apk — 로컬 1차 검사

검사일: 2026-09-15. APK 실행·설치 및 외부 웹/게임/CDN 접속 없음.

## 입력과 구조

- 입력: `C:\Users\NHN\Downloads\com.blgg.java800.com.apk`
- 크기: 1,251,987 bytes. ZIP 엔트리 133개.
- `classes.dex`~`classes12.dex`, `lib/armeabi/libluajava.so` 포함.
- 앱 assets: Lua 파일 8개, 아이콘/시작 이미지와 drawable 엔트리.
- DEX 문자열에 AndroLua, LuaWebView, MyWebView 등 존재.
- `assets/config.lua`는 Lua 5.3 바이트코드 헤더. 다른 앱 Lua 7개는 일반 Lua 헤더가 아닌 변환된 바이트열이며 아직 해독하지 않았다.

## 핵심 근거

`assets/config.lua`의 상수 문자열에 `web`, `启动网页`(시작 웹페이지),
아래 외부 페이지 주소가 인접해 있다. 주소는 파일에서 읽기만 했고 접속하지 않았다.

```text
https://incubator-static.easygame2021.com/screw-puzzle/guest/315/webpackage/index.html
```

같은 설정에는 브라우저 사용자 식별자·진행바·상태바 설정, 페이지 로드 이벤트,
java800 사이트의 다운로드 안내 문구가 들어 있다.
주소 경로는 screw-puzzle을 가리키지만 공식 게임명/제작사/버전은 검증하지 않았다.

## 판정 및 한계

외부 웹 게임을 여는 AndroLua/WebView 래퍼로 판단된다. APK 엔트리 목록에는
게임용 HTML·JavaScript·레벨 테이블·대형 게임 리소스가 확인되지 않았다.
이는 Clash처럼 로컬 암호화 패키지에 본게임 데이터가 포함된 상황과 다르다.
DEX 전체 역분석 및 변환 Lua 7개 해독은 하지 않았으므로 숨겨진 모든 데이터의
부재나 앱의 보안성을 보증하는 결과는 아니다.

현재 APK만으로 밸런스·레벨을 추출했다고 주장할 수 없다. URL이 들어 있다는
이유로 자동 접속하지 않는다. 기존의 게임사 접촉 금지 범위에서는 여기서
네트워크 작업을 멈춘다. 사용자가 이미 보유한 웹 패키지, 게임 JS/JSON 또는
이전에 저장한 캐시 파일을 제공하면 그 로컬 사본을 이어서 분석할 수 있다.

원본 APK는 수정하지 않았다. 앱 설치·런치·권한 부여·온라인 탐지 회피·Dooray 게시 없음.
