import { useState } from "react";
import { formatNpr } from "../data/options";
import { logClick } from "../services/api";
import "./FavoritesSection.css";

function FavCard({ fav, onOpen, onRemove, productType }) {
  const { laptop, score, deal } = fav;
  const isPhone = productType === "phone";

  const title = isPhone
    ? (laptop.product_name || `${laptop.brand} ${laptop.chipset || ""}`)
    : `${laptop.brand} ${laptop.cpu_model}`;

  return (
    <article className="fav-card">
      <div className="fav-card__head">
        <h4>{title}</h4>
        {score != null && (
          <span className="fav-card__score">{Math.round(score)}%</span>
        )}
      </div>
      <div className="fav-card__specs">
        {isPhone ? (
          <>
            {laptop.chipset && <span className="spec-pill">🧠 {laptop.chipset}</span>}
            <span className="spec-pill">⚡ {laptop.ram_gb} GB RAM</span>
            {laptop.battery_mah > 0 && <span className="spec-pill">🔋 {laptop.battery_mah} mAh</span>}
            {laptop.rear_camera_mp > 0 && <span className="spec-pill">📸 {laptop.rear_camera_mp} MP</span>}
          </>
        ) : (
          <>
            <span className="spec-pill">⚡ {laptop.ram_gb} GB RAM</span>
            {laptop.storage_gb > 0 && (
              <span className="spec-pill">
                💾 {laptop.storage_gb >= 1024 ? `${laptop.storage_gb / 1024} TB` : `${laptop.storage_gb} GB`} {laptop.storage_type}
              </span>
            )}
          </>
        )}
        {deal?.tier === "great" && (
          <span className="deal-badge deal-badge--great">🏷️ Great deal</span>
        )}
      </div>
      <div className="fav-card__footer">
        <span className="fav-card__price">{formatNpr(laptop.price_npr)}</span>
        <div className="fav-card__actions">
          <button type="button" className="btn-details" onClick={() => onOpen(fav)}>
            View
          </button>
          <button
            type="button"
            className="fav-card__remove"
            aria-label="Remove from saved"
            onClick={() => onRemove(fav)}
          >
            Remove
          </button>
        </div>
      </div>
    </article>
  );
}

function FavSection({ title, eyebrow, items, onOpen, onRemove, productType }) {
  const [gone, setGone] = useState([]);
  const list = items.filter((f) => !gone.includes(f.id));

  function handleRemove(fav) {
    logClick("favorite_remove", null, { brand: fav.laptop.brand });
    onRemove(fav);
    setGone((g) => [...g, fav.id]);
  }

  if (list.length === 0) return null;

  return (
    <section className="section saved" id={productType === "phone" ? "saved-phones" : "saved"}>
      <div className="container">
        <div className="section-head saved__head">
          <span className="eyebrow">{eyebrow}</span>
          <h2>{title}</h2>
          <p>Tap Remove to drop one — they stay saved even if you close the tab.</p>
        </div>

        <div className="saved__grid">
          {list.map((fav) => (
            <FavCard
              key={fav.id}
              fav={fav}
              onOpen={(f) => onOpen({ ...f, _rank: null })}
              onRemove={handleRemove}
              productType={productType}
            />
          ))}
        </div>
        <div className="saved__actions">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              logClick("favorite_clear", null, { count: list.length });
              items.forEach((f) => onRemove(f));
              setGone(list.map((f) => f.id));
            }}
          >
            Clear saved {productType === "phone" ? "phones" : "laptops"}
          </button>
        </div>
      </div>
    </section>
  );
}

export default function FavoritesSection({ favorites, onOpen, onRemove }) {
  if (!favorites || favorites.length === 0) return null;

  const laptops = favorites.filter((f) => (f.productType || "laptop") === "laptop");
  const phones = favorites.filter((f) => f.productType === "phone");

  return (
    <>
      {laptops.length > 0 && (
        <FavSection
          title="Laptops you saved for later."
          eyebrow="💖 Your Saved Laptops"
          items={laptops}
          onOpen={onOpen}
          onRemove={onRemove}
          productType="laptop"
        />
      )}
      {phones.length > 0 && (
        <FavSection
          title="Phones you saved for later."
          eyebrow="📱 Your Saved Phones"
          items={phones}
          onOpen={onOpen}
          onRemove={onRemove}
          productType="phone"
        />
      )}
    </>
  );
}
