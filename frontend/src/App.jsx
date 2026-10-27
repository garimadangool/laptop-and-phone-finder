import { useEffect, useState } from "react";
import { getStats, getPhoneStats, logClick } from "./services/api";
import { getFavorites, toggleFavorite as persistFavorite, clearFavorites, favoriteId } from "./services/favorites";
import { useViewRedirect } from "./hooks/useViewRedirect";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import HowItWorks from "./components/HowItWorks";
import FinderSection from "./components/FinderSection";
import ResultsSection from "./components/ResultsSection";
import FavoritesSection from "./components/FavoritesSection";
import InsightsSection from "./components/InsightsSection";
import LaptopDetail from "./components/LaptopDetail";
import PhoneDetail from "./components/PhoneDetail";
import CompareTray from "./components/CompareTray";
import CompareModal from "./components/CompareModal";
import ScrollToTop from "./components/ScrollToTop";
import Footer from "./components/Footer";

export default function App() {
  useViewRedirect();

  const [productType, setProductType] = useState("laptop");
  const [results, setResults] = useState([]);
  const [stats, setStats] = useState(null);
  const [phoneStats, setPhoneStats] = useState(null);
  const [detailRec, setDetailRec] = useState(null);
  const [compare, setCompare] = useState([]);
  const [compareOpen, setCompareOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const [favorites, setFavorites] = useState(() => getFavorites());

  function handleResults(recs) {
    setResults(recs);
    setCompare([]);
    setCompareOpen(false);
  }

  function openDetails(rec) {
    logClick("view_details", rec);
    setDetailRec(rec);
  }

  function openAskAiSource(src) {
    if (!src || !src.laptop) return;
    logClick("view_source", null, {
      brand: src.laptop.brand,
      cpu_model: src.laptop.cpu_model,
      price_npr: src.laptop.price_npr,
    });
    setDetailRec({
      laptop: src.laptop,
      score: Math.round((src.similarity ?? 0) * 100),
      reasons: [],
      penalties: [],
      deal: null,
    });
  }

  function toggleCompare(rec) {
    const adding = !compare.includes(rec);
    logClick(adding ? "compare_add" : "compare_remove", rec);
    setCompare((prev) =>
      prev.includes(rec)
        ? prev.filter((r) => r !== rec)
        : prev.length >= 4
          ? prev
          : [...prev, rec]
    );
  }

  function toggleSaved(rec) {
    const wasSaved = favorites.some((f) => f.id === favoriteId(rec, productType));
    logClick(wasSaved ? "favorite_remove" : "favorite_add", rec);
    const next = persistFavorite(rec, productType);
    setFavorites(next);
    return next;
  }

  function removeSaved(fav, clearAll = false) {
    if (clearAll) {
      setFavorites(clearFavorites());
      return;
    }
    const next = favorites.filter((f) => f.id !== fav.id);
    setFavorites(next);
    try {
      localStorage.setItem("laptopfinder.favorites.v2", JSON.stringify(next));
    } catch { /* ignore */ }
  }

  function switchProductType(type) {
    setProductType(type);
    setResults([]);
    setCompare([]);
    setCompareOpen(false);
    setDetailRec(null);
    requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  useEffect(() => {
    let cancelled = false;
    getStats()
      .then((data) => { if (!cancelled) setStats(data); })
      .catch(() => {});
    getPhoneStats()
      .then((data) => { if (!cancelled) setPhoneStats(data); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const activeStats = productType === "phone" ? phoneStats : stats;

  return (
    <>
      <Navbar productType={productType} onSwitch={switchProductType} />
      <main>
        <Hero stats={activeStats} productType={productType} />
        <HowItWorks productType={productType} />
        <FinderSection onResults={handleResults} onLoadingChange={setSearching} productType={productType} />
        <ResultsSection
          results={results}
          loading={searching}
          onViewDetails={openDetails}
          compare={compare}
          onToggleCompare={toggleCompare}
          favorites={favorites}
          onToggleFavorite={toggleSaved}
          productType={productType}
        />
        <FavoritesSection
          favorites={favorites}
          onOpen={(fav) => openDetails(fav)}
          onRemove={removeSaved}
        />
        <InsightsSection productType={productType} />
      </main>
      {detailRec && productType === "laptop" && (
        <LaptopDetail
          rec={detailRec}
          onClose={() => setDetailRec(null)}
          onToggleCompare={toggleCompare}
          isFavorited={favorites.some((f) => f.id === favoriteId(detailRec, "laptop"))}
          onToggleFavorite={toggleSaved}
          onViewLaptop={openAskAiSource}
        />
      )}
      {detailRec && productType === "phone" && (
        <PhoneDetail
          rec={detailRec}
          onClose={() => setDetailRec(null)}
          onToggleCompare={toggleCompare}
          isFavorited={favorites.some((f) => f.id === favoriteId(detailRec, "phone"))}
          onToggleFavorite={toggleSaved}
        />
      )}
      {!compareOpen && compare.length > 0 && (
        <CompareTray
          items={compare}
          onOpen={() => setCompareOpen(true)}
          onClear={() => setCompare([])}
        />
      )}
      {compareOpen && compare.length >= 2 && (
        <CompareModal items={compare} onClose={() => setCompareOpen(false)} productType={productType} />
      )}
      <ScrollToTop />
      <Footer />
    </>
  );
}
