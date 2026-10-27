// Favourites / shortlist — persisted to localStorage so saved devices
// survive page reloads and browser restarts. Pure client-side, no PII.

const KEY = "laptopfinder.favorites.v2";

function read() {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(list) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    /* storage full / private mode — silently ignore */
  }
}

// A stable identity for a recommendation row.
export function favoriteId(rec, productType) {
  const { laptop } = rec;
  if (productType === "phone" || laptop.has_5g !== undefined || laptop.chipset !== undefined || laptop.battery_mah !== undefined) {
    return [
      "phone",
      laptop.brand,
      laptop.product_name,
      laptop.chipset,
      laptop.ram_gb,
      laptop.storage_gb,
      laptop.price_npr,
    ].join("|");
  }
  return [
    "laptop",
    laptop.brand,
    laptop.cpu_model,
    laptop.ram_gb,
    laptop.storage_gb,
    laptop.price_npr,
  ].join("|");
}

export function getFavorites() {
  return read();
}

export function isFavorited(rec, productType) {
  const id = favoriteId(rec, productType);
  return read().some((f) => f.id === id);
}

// Returns the new favourites array.
export function toggleFavorite(rec, productType) {
  const id = favoriteId(rec, productType);
  const { laptop, score, deal, reasons, penalties } = rec;
  const current = read();
  const exists = current.find((f) => f.id === id);

  let next;
  if (exists) {
    next = current.filter((f) => f.id !== id);
  } else {
    next = [
      {
        id,
        productType: productType || "laptop",
        savedAt: Date.now(),
        score: score ?? null,
        deal: deal ?? null,
        reasons: Array.isArray(reasons) ? reasons : [],
        penalties: Array.isArray(penalties) ? penalties : [],
        laptop,
      },
      ...current,
    ];
  }
  write(next);
  return next;
}

export function clearFavorites() {
  write([]);
  return [];
}
