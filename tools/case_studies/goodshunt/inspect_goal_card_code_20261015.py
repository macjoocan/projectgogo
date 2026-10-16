from pathlib import Path
p=Path(__file__).resolve().parent;source=p/'inspect_growth_fx_code_20261015.py';s=source.read_text(encoding='utf-8')
s=s.replace("out=p/'growth_fx_code_audit_20261015'","out=p/'goal_card_code_audit_20261015'")
lines=s.splitlines();hits=[i for i,line in enumerate(lines) if line.startswith("  if ('class LevelBehavior.")];assert len(hits)==1
lines[hits[0]]="  if ('class GoalCard' in cur or 'struct GoalCard.' in cur or 'class CardController.' in cur or 'struct CardController.' in cur or ('class CardController ' in cur and any(t in line for t in ('OnRemoveCard(', 'OnRearrangeCard(', 'AnimateCards(', 'CoroutineAnimateCards(', 'DoPunchCard(', '<OnRearrangeCard>b__55_0(')))):want.append(a)"
exec(compile('\n'.join(lines),str(source),'exec'))
