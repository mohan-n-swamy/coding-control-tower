const SECTIONS = [
  { key: "active", label: "ACTIVE", mascot: "watching", cls: "" },
  { key: "attention", label: "NEEDS MOHAN'S ACTION", mascot: "attention", cls: "amber" },
  { key: "planning", label: "PLANNING", mascot: "planning", cls: "" },
  { key: "idle", label: "ARCHIVE · NOT ACTIVE", mascot: "idle", cls: "dim" }
];
function Projects({ data }) {
  return SECTIONS.map(s => {
    const ps = data.projects.filter(p => p.state === s.key);
    if (!ps.length) return null;
    return (
      <div className={"sect sect-" + s.key} key={s.key}>
        <div className="ml-row sect-head"><Mascot state={s.mascot} size={40} /><div className={"bandlabel " + s.cls}>{s.label} · {ps.length}</div></div>
        <div className="sect-body">
          {ps.map(p => <div key={p.id} id={"proj-" + p.id}><ProjectPanel p={p} defaultOpen={p.id === data.now.projectId} activePr={p.id === data.now.projectId ? data.now.pr : null} /></div>)}
        </div>
      </div>
    );
  });
}
function VariantCockpit({ data }) {
  return (
    <div className="v-cockpit">
      <header className="topbar">
        <Mascot state="watching" size={38} />
        <span className="wordmark">CODING CONTROL TOWER</span>
        <span className="tagline">design coding · work ledger</span>
        <span className="clock">Tue Jul 14 · 10:52</span>
      </header>
      <section className="nowband" aria-label="Now">
        <div className="nb-art"><MascotHero state="working" /><span className="nb-state">WORKING</span></div>
        <div className="nb-facts"><div className="bandlabel">NOW</div><NowFacts now={data.now} /></div>
        <div className="nb-usage"><div className="bandlabel dim">MODEL USAGE · TODAY</div><ModelUsage usage={data.usage} /></div>
      </section>
      <section className="mohanband" aria-label="Needs Mohan">
        <div className="ml-row"><Mascot state="attention" size={44} /><div className="bandlabel amber">NEEDS MOHAN · {data.needsMohan.length}</div></div>
        <div className="mohan-row">{data.needsMohan.map((m, i) => <MohanItem key={i} m={m} />)}</div>
      </section>
      <div className="bandlabel dim hist">HISTORY — ALL PROJECTS</div>
      <main className="stack"><Projects data={data} /></main>
      <footer className="foot">READ-ONLY LEDGER · 4 PROJECTS · REFRESHED TUE JUL 14 · 10:52</footer>
    </div>
  );
}
function VariantRail({ data }) {
  return (
    <div className="v-rail">
      <aside className="rail">
        <div className="rail-brand"><Mascot state="watching" size={48} /><div><span className="wordmark">CODING<br />CONTROL TOWER</span><span className="tagline">work ledger</span></div></div>
        <div className="rail-now"><MascotHero state="working" /><div className="bandlabel">NOW · WORKING</div><NowFacts now={data.now} compact /></div>
        <div className="rail-mohan"><div className="ml-row"><Mascot state="attention" size={36} /><div className="bandlabel amber">NEEDS MOHAN · {data.needsMohan.length}</div></div>
          {data.needsMohan.map((m, i) => <MohanItem key={i} m={m} />)}</div>
        <div className="rail-usage"><div className="bandlabel dim">MODEL USAGE · TODAY</div><ModelUsage usage={data.usage} /></div>
        <nav className="rail-nav" aria-label="Projects">
          <div className="bandlabel dim">PROJECTS</div>
          {data.projects.map(p => (
            <a key={p.id} className={"rn-item rn-" + p.state} href={"#proj-" + p.id}>
              <Mascot state={PROJ_MASCOT[p.state] || "idle"} size={30} /><span>{p.name}</span><em>{p.activity}</em>
            </a>))}
        </nav>
        <div className="rail-foot">read-only · Tue Jul 14 · 10:52</div>
      </aside>
      <main className="rail-main">
        <div className="bandlabel dim hist">HISTORY — ALL PROJECTS</div>
        <Projects data={data} />
      </main>
    </div>
  );
}
function VariantGrid({ data }) {
  const totals = { active: 1, merged: 10, failed: 2, mohan: data.needsMohan.length };
  return (
    <div className="v-grid">
      <header className="ticker">
        <Mascot state="watching" size={34} />
        <span className="wordmark">CODING CONTROL TOWER</span>
        <span className="tk-sep"></span>
        <span className="tk-stat"><Led tone="active" />1 active</span>
        <span className="tk-stat"><Led tone="merged" />{totals.merged} merged</span>
        <span className="tk-stat"><Led tone="failed" />{totals.failed} failed</span>
        <span className="tk-stat"><Led tone="attention" />{totals.mohan} need Mohan</span>
        <span className="clock">Tue Jul 14 · 10:52</span>
      </header>
      <section className="hero-row">
        <div className="hero-now">
          <MascotHero state="working" label="WORKING" />
          <div className="bandlabel" style={{ margin: "12px 0" }}>NOW</div>
          <NowFacts now={data.now} />
        </div>
        <div className="hero-mohan">
          <MascotHero state="attention" label={"NEEDS MOHAN · " + totals.mohan} />
          {data.needsMohan.map((m, i) => <MohanItem key={i} m={m} />)}
        </div>
        <div className="hero-usage"><div className="bandlabel dim">MODEL USAGE · TODAY</div><ModelUsage usage={data.usage} /></div>
      </section>
      <div className="bandlabel dim hist">HISTORY — ALL PROJECTS</div>
      <main className="tilegrid"><Projects data={data} /></main>
      <footer className="foot">READ-ONLY LEDGER · 4 PROJECTS · REFRESHED TUE JUL 14 · 10:52</footer>
    </div>
  );
}
Object.assign(window, { VariantCockpit, VariantRail, VariantGrid });
