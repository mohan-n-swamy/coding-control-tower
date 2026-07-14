const { useState } = React;
const MASCOT_IMG = { watching: "uploads/01-mascot-watching-106cfdfd.png", planning: "uploads/01-mascot-watching-106cfdfd.png", working: "uploads/05-harness-hero-reference-c1e131d9.png", attention: "uploads/02-mascot-concerned-d0f0f469.png", happy: "uploads/03-mascot-happy-75f3cd46.png", idle: "uploads/04-mascot-sleeping-b46154f4.png" };
const PROJ_MASCOT = { active: "watching", attention: "attention", planning: "planning", idle: "idle" };
function Mascot({ state = "working", size = 44 }) {
  return (
    <div className={"mascot m-" + state} style={{ width: size, height: size }} aria-hidden="true">
      <img src={MASCOT_IMG[state] || MASCOT_IMG.working} alt="" />
      <i className="m-dot"></i>
    </div>
  );
}
function MascotHero({ state = "working", label }) {
  return (
    <div className={"mhero mh-" + state} aria-hidden="true">
      <img src={MASCOT_IMG[state] || MASCOT_IMG.working} alt="" />
      {label && <span className="mh-label">{label}</span>}
    </div>
  );
}
function Led({ tone }) { return <i className={"led led-" + tone}></i>; }
function Pill({ tone, children }) { return <span className={"pill pill-" + tone}>{children}</span>; }
function VBadges({ list }) {
  if (!list || !list.length) return null;
  return (
    <div className="vrow">
      {list.map((v, i) => v.href
        ? <a key={i} className={"vb vb-" + v.tone} href={v.href}>{v.label} ↗</a>
        : <span key={i} className={"vb vb-" + v.tone}>{v.label}</span>)}
    </div>
  );
}
function TaskMeter({ tasks }) {
  const pct = Math.round((tasks.done / tasks.total) * 100);
  return (
    <div className="tmeter" title={tasks.done + "/" + tasks.total + " tasks"}>
      <span className="tnum">{tasks.done}/{tasks.total}</span>
      <span className="tbar"><i style={{ width: pct + "%" }}></i></span>
    </div>
  );
}
function ErrorBox({ error }) {
  return (
    <div className="errbox">
      <div><b>Cause</b><span>{error.cause}</span></div>
      <div><b>Impact</b><span>{error.impact}</span></div>
      <div><b>Next</b><span>{error.next}</span></div>
    </div>
  );
}
function PRItem({ pr, defaultOpen }) {
  const [open, setOpen] = useState(!!defaultOpen);
  const tone = pr.status;
  return (
    <div className={"pr pr-" + tone + (open ? " is-open" : "")}>
      <button className="prhead" aria-expanded={open} onClick={() => setOpen(!open)}>
        <Led tone={tone} />
        <span className="prnum">#{pr.num}</span>
        <span className="prtitle">{pr.title}</span>
        <Pill tone={tone}>{pr.statusLabel}</Pill>
        <span className="prdate">{pr.date}{pr.updated ? " · " + pr.updated : ""}</span>
        {pr.tasks && <TaskMeter tasks={pr.tasks} />}
        <span className="chev">▾</span>
      </button>
      {open && (
        <div className="prbody">
          <div className="prcol">
            {pr.outcome && <div className="fact"><label>Delivered outcome</label><p>{pr.outcome}</p></div>}
            {pr.progress && <div className="fact"><label>Where it stands</label><p>{pr.progress}</p></div>}
            {pr.error && <div className="fact"><label>Failure</label><ErrorBox error={pr.error} /></div>}
            <div className="fact"><label>Verification</label><VBadges list={pr.verification} /></div>
          </div>
          <div className="prcol">
            {pr.tasks && pr.tasks.items && (
              <div className="fact"><label>Tasks</label>
                <ul className="tlist">{pr.tasks.items.map((it, i) =>
                  <li key={i} className={it.done ? "done" : ""}><i>{it.done ? "✓" : "○"}</i>{it.t}</li>)}</ul>
              </div>)}
            {pr.runs && (
              <div className="fact"><label>Runs</label>
                <ul className="runs">{pr.runs.map((r, i) =>
                  <li key={i}><i className={"led led-" + (r.ok ? "merged" : "failed")}></i><code>{r.label}</code><span>{r.time}</span></li>)}</ul>
              </div>)}
          </div>
        </div>
      )}
    </div>
  );
}
function LocalWork({ items }) {
  if (!items || !items.length) return null;
  return (
    <div className="localwork">
      <div className="lwhead">No-PR work</div>
      {items.map((w, i) => (
        <div className="lwitem" key={i}><Led tone="local" /><span className="lwt">{w.t}</span><span className="lwnote">{w.note}</span><span className="lwdate">{w.date}</span></div>
      ))}
    </div>
  );
}
function ProjectPanel({ p, defaultOpen, activePr }) {
  const [open, setOpen] = useState(!!defaultOpen);
  return (
    <section className={"proj proj-" + p.state + (open ? " is-open" : "")}>
      <button className="projhead" aria-expanded={open} onClick={() => setOpen(!open)}>
        <Mascot state={PROJ_MASCOT[p.state] || "idle"} size={52} />
        <span className="pname">{p.name}</span>
        <span className="ppath">{p.path} · <b>{p.branch}</b></span>
        <span className="pcounts">{p.counts}</span>
        <span className="pact">{p.activity}</span>
        <span className="chev">▾</span>
      </button>
      {open && (
        <div className="projbody">
          <div className="timeline">
            {p.prs.map(pr => <PRItem key={pr.num} pr={pr} defaultOpen={pr.num === activePr} />)}
          </div>
          <LocalWork items={p.local} />
        </div>
      )}
    </section>
  );
}
function MohanItem({ m }) {
  return (
    <div className="mohan-item">
      <Led tone="attention" />
      <div className="mi-body">
        <div className="mi-ask">{m.ask}</div>
        <div className="mi-meta"><code>{m.project}</code><span>blocks {m.blocks}</span></div>
      </div>
      <span className="mi-age">{m.age}</span>
    </div>
  );
}
function NowFacts({ now, compact }) {
  return (
    <div className={"nowfacts" + (compact ? " nf-compact" : "")}>
      <div className="fact"><label>Working on</label><p><b>{now.task}</b> — PR #{now.pr} · <code>{now.project}</code></p></div>
      <div className="fact"><label>Stopped at</label><p>{now.stop}</p></div>
      <div className="fact"><label>Next action</label><p className="nextact">▸ {now.next}</p></div>
      <div className="nowmeta"><span>started {now.started}</span><span>{now.elapsed} elapsed</span><span>last run: <code>{now.lastRun}</code></span><span>model: <code>claude-sonnet-4-5</code></span></div>
    </div>
  );
}
function ModelUsage({ usage }) {
  return (
    <div className="usage">
      <div className="us-total"><span>{usage.totalIn} in</span><span>{usage.totalOut} out</span></div>
      {usage.models.map((m, i) => (
        <div className="us-row" key={i}>
          <span className="us-prov">{m.provider}</span>
          <span className="us-model">{m.model}</span>
          <span className="us-tok">{m.tin} / {m.tout}</span>
          <span className="us-bar"><i style={{ width: m.share + "%" }}></i></span>
        </div>
      ))}
    </div>
  );
}
Object.assign(window, { Mascot, MascotHero, Led, Pill, VBadges, ModelUsage, PROJ_MASCOT, TaskMeter, ErrorBox, PRItem, LocalWork, ProjectPanel, MohanItem, NowFacts });
