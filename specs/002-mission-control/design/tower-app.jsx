const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "layout": "Mission grid",
  "accent": "#b7a8f2",
  "density": "compact"
}/*EDITMODE-END*/;
function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const data = window.TOWER_DATA;
  React.useEffect(() => {
    document.documentElement.style.setProperty("--acc", t.accent);
    document.body.dataset.density = t.density;
  }, [t.accent, t.density]);
  const V = t.layout === "Split rail" ? VariantRail : t.layout === "Mission grid" ? VariantGrid : VariantCockpit;
  return (
    <React.Fragment>
      <V key={t.layout} data={data} />
      <TweaksPanel>
        <TweakSection label="Layout" />
        <TweakRadio label="Variant" value={t.layout} options={["Cockpit", "Split rail", "Mission grid"]} onChange={v => setTweak("layout", v)} />
        <TweakSection label="Theme" />
        <TweakColor label="Accent" value={t.accent} options={["#86d3f4", "#8fe6c0", "#b7a8f2", "#f2c894"]} onChange={v => setTweak("accent", v)} />
        <TweakRadio label="Density" value={t.density} options={["regular", "compact"]} onChange={v => setTweak("density", v)} />
      </TweaksPanel>
    </React.Fragment>
  );
}
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
