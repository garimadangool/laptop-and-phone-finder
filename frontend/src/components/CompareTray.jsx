import "./CompareTray.css";

export default function CompareTray({ items, onOpen, onClear }) {
  return (
    <div className="compare-tray" role="region" aria-label="Comparison selection">
      <div className="compare-tray__chips">
        {items.map((rec) => (
          <span key={rec.laptop.brand + rec.laptop.cpu_model} className="compare-tray__chip">
            {rec.laptop.brand}
          </span>
        ))}
      </div>
      <button type="button" className="compare-tray__clear" onClick={onClear}>
        Clear
      </button>
      <button
        type="button"
        className="compare-tray__open"
        onClick={onOpen}
        disabled={items.length < 2}
        title={items.length < 2 ? "Pick at least two laptops" : "Open side-by-side comparison"}
      >
        ⇄ Compare ({items.length})
      </button>
    </div>
  );
}
