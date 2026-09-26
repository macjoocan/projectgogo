#!/usr/bin/env node
// 스테이징 범위 경고 — 이 레포의 실제 사고를 막는다.
//
// 배경: 한 세션이 `git add -A` 로 스테이징했다가 다른 세션의 진행 중 파일까지
// 커밋·푸시한 사고가 실제로 있었다. 브랜치를 판다고 막히지 않는다 — 세션들이
// 같은 체크아웃을 공유하기 때문이다. 막는 지점은 **스테이징 범위**다.
//
// 동시 세션이 없는 환경에서도 유효하다: 이 작업트리에는 추적되지 않는 분석
// 산출물과 임시 스크립트가 상시 존재한다.
//
// 차단하지 않는다. 경고만 띄우고 판단은 사람에게 맡긴다.
//
// 판정은 명령의 **따옴표 앞부분**(옵션 영역)에서만 한다 —
// `git commit -m "add -a to the list"` 같은 메시지 본문에 걸리지 않게.

let raw = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (d) => (raw += d));
process.stdin.on("end", () => {
  let cmd = "";
  try {
    cmd = JSON.parse(raw)?.tool_input?.command ?? "";
  } catch {
    process.exit(0); // 입력을 못 읽으면 조용히 통과 — 훅이 작업을 막으면 안 된다
  }

  const head = cmd.split('"')[0].split("'")[0];
  const hits = [];
  if (/git +add +(-A\b|--all\b|\.( |$))/.test(head))
    hits.push("`git add -A` / `--all` / `.` — 지금 작업트리에 있는 **전부**를 스테이징한다");
  if (/git +commit +(.* )?-[a-zA-Z]*a[a-zA-Z]*( |$)/.test(head))
    hits.push("`git commit -a` — 추적 중인 파일을 **전부** 커밋한다");
  if (/git +commit +(.* )?--all( |$)/.test(head))
    hits.push("`git commit --all` — 추적 중인 파일을 **전부** 커밋한다");

  if (hits.length === 0) process.exit(0);

  const msg =
    "[스테이징 범위 주의]\n" +
    hits.map((h) => "  · " + h).join("\n") +
    "\n\n이 레포에서 실제로 사고가 났다 — 다른 세션의 진행 중 파일이 딸려 들어가 " +
    "커밋·푸시됐다.\n작업트리에는 추적되지 않는 분석 산출물·임시 파일이 상시 있다.\n" +
    "  -> 경로를 명시해라:  git add <경로> [<경로>...]\n" +
    "  -> 지금 뭐가 열려 있는지:  git status --short";

  process.stdout.write(JSON.stringify({ systemMessage: msg }));
  process.exit(0);
});
