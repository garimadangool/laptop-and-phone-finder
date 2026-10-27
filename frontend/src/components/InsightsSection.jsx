import { useEffect, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, LabelList,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { getInsights, getPhoneInsights } from "../services/api";
import "./InsightsSection.css";

const PRIMARY = "#2337b8";
const VIOLET = "#7c3aed";
const MUTED = "#5b6178";
const GRID_LINE = "#e9e4d9";
const PIE_COLORS = ["#2337b8", "#7c3aed", "#f59e0b", "#15803d", "#c2410c", "#0284c7", "#db2777", "#0d9488"];
const AXIS_TICK = { fontSize: 11, fill: MUTED };

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function fmtCompact(npr) {
  if (npr >= 100000) { const lakh = npr / 100000; return `${lakh % 1 === 0 ? lakh : lakh.toFixed(1)}L`; }
  if (npr >= 1000) return `${Math.round(npr / 1000)}K`;
  return String(npr);
}

function fmtFull(npr) { return `NPR ${Math.round(npr).toLocaleString("en-IN")}`; }
function truncate(text, max = 16) { return text.length > max ? `${text.slice(0, max - 1)}…` : text; }

function ChartTip({ active, payload }) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0].payload;
  return (
    <div className="chart-tip">
      <p className="chart-tip__label">{row.name}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="chart-tip__value">
          <span className="chart-tip__dot" style={{ background: entry.color || entry.stroke || PRIMARY }} />
          {entry.dataKey === "Avg price" ? fmtFull(entry.value) : `${entry.value.toLocaleString("en-IN")} items`}
        </p>
      ))}
      {typeof row.Laptops === "number" && (
        <p className="chart-tip__sub">Based on {row.Laptops.toLocaleString("en-IN")} items</p>
      )}
    </div>
  );
}

function ChartCard({ title, subtitle, wide, children, ariaLabel }) {
  return (
    <article className={`chart-card${wide ? " chart-card--wide" : ""}`} role="img" aria-label={ariaLabel}>
      <header className="chart-card__head"><h3>{title}</h3>{subtitle && <p>{subtitle}</p>}</header>
      {children}
    </article>
  );
}

export default function InsightsSection({ productType = "laptop" }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retryToken, setRetryToken] = useState(0);
  const [reducedMotion] = useState(prefersReducedMotion);
  const isPhone = productType === "phone";
  const [prevIsPhone, setPrevIsPhone] = useState(isPhone);

  // Reset loading state when switching product type
  if (isPhone !== prevIsPhone) {
    setPrevIsPhone(isPhone);
    setData(null);
    setError(null);
    setLoading(true);
  }

  useEffect(() => {
    let cancelled = false;
    const fetcher = isPhone ? getPhoneInsights : getInsights;
    fetcher()
      .then((d) => { if (!cancelled) setData(d); })
      .catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [isPhone, retryToken]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setRetryToken((t) => t + 1);
  }

  const animate = !reducedMotion;

  if (isPhone) {
    const priceData = data?.price_histogram?.map((d) => ({ name: d.bucket, Laptops: d.count })) ?? [];
    const brandData = data?.top_brands?.map((d) => ({ name: d.brand, Laptops: d.count })) ?? [];
    const purposeData = data?.purpose_distribution?.map((d) => ({ name: d.purpose, Laptops: d.count })) ?? [];
    const chipTierData = data?.chipset_tier_distribution?.map((d) => ({ name: `Tier ${d.tier}`, Phones: d.count })) ?? [];
    const chipFamilyData = data?.chipset_family_distribution?.slice(0, 8)?.map((d) => ({ name: d.family, Phones: d.count })) ?? [];
    const horizontalHeight = Math.max(brandData.length, purposeData.length);

    return (
      <section id="insights" className="section insights">
        <div className="container">
          <div className="section-head">
            <span className="eyebrow">📊 Phone Market Insights</span>
            <h2>The Nepali phone market, visualized</h2>
            <p>Live charts from our dataset of {(data?.total_phones ?? 3328).toLocaleString("en-IN")} phones.</p>
          </div>

          {error && !data && (
            <div className="insights__state" role="alert">
              <span className="insights__state-icon" aria-hidden="true">📉</span>
              <h3>Couldn&apos;t load the charts</h3>
              <p>{error}</p>
              <button type="button" className="btn btn-primary" onClick={handleRetry}>Try again</button>
            </div>
          )}

          {loading && !data && !error && (
            <div className="insights__grid" aria-hidden="true">
              <div className="skel-card skel-card--wide" />
              <div className="skel-card" />
              <div className="skel-card" />
            </div>
          )}

          {data && (
            <div className="insights__grid">
              <ChartCard wide title="Price landscape" subtitle="How many phones fall into each NPR price band" ariaLabel="Histogram of phone prices">
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={priceData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="priceFillP" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={PRIMARY} stopOpacity={0.35} />
                        <stop offset="100%" stopColor={PRIMARY} stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_LINE} />
                    <XAxis dataKey="name" tick={AXIS_TICK} tickLine={false} axisLine={{ stroke: GRID_LINE }} interval={2} tickFormatter={(v) => v.endsWith("+") ? v : v.split("-")[0]} />
                    <YAxis allowDecimals={false} tick={AXIS_TICK} tickLine={false} axisLine={false} width={42} />
                    <Tooltip content={<ChartTip />} cursor={{ stroke: VIOLET, strokeDasharray: "4 4" }} />
                    <Area type="monotone" dataKey="Laptops" stroke={PRIMARY} strokeWidth={2.5} fill="url(#priceFillP)" isAnimationActive={animate} />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Top brands" subtitle="Phones in dataset by brand" ariaLabel="Top phone brands">
                <ResponsiveContainer width="100%" height={horizontalHeight * 32 + 30}>
                  <BarChart data={brandData} layout="vertical" margin={{ top: 0, right: 42, left: 0, bottom: 0 }}>
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="name" tick={{ ...AXIS_TICK, fontSize: 12 }} tickLine={false} axisLine={false} width={86} />
                    <Tooltip content={<ChartTip />} cursor={{ fill: "rgba(35,55,184,0.06)" }} />
                    <Bar dataKey="Laptops" fill={PRIMARY} radius={[0, 7, 7, 0]} barSize={16} isAnimationActive={animate}>
                      <LabelList dataKey="Laptops" position="right" style={{ fontSize: 11, fill: MUTED }} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Purpose distribution" subtitle="Which use cases our dataset covers most" ariaLabel="Phone purpose distribution">
                <ResponsiveContainer width="100%" height={horizontalHeight * 32 + 30}>
                  <BarChart data={purposeData} layout="vertical" margin={{ top: 0, right: 42, left: 0, bottom: 0 }}>
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="name" tick={{ ...AXIS_TICK, fontSize: 12 }} tickFormatter={(v) => truncate(v)} tickLine={false} axisLine={false} width={128} />
                    <Tooltip content={<ChartTip />} cursor={{ fill: "rgba(124,58,237,0.06)" }} />
                    <Bar dataKey="Laptops" fill={VIOLET} radius={[0, 7, 7, 0]} barSize={16} isAnimationActive={animate}>
                      <LabelList dataKey="Laptops" position="right" style={{ fontSize: 11, fill: MUTED }} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Chipset tier distribution" subtitle="How phones spread across our 1-6 performance tiers" ariaLabel="Chipset tier distribution">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={chipTierData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_LINE} />
                    <XAxis dataKey="name" tick={AXIS_TICK} tickLine={false} axisLine={{ stroke: GRID_LINE }} />
                    <YAxis allowDecimals={false} tick={AXIS_TICK} tickLine={false} axisLine={false} width={42} />
                    <Tooltip content={<ChartTip />} cursor={{ fill: "rgba(35,55,184,0.06)" }} />
                    <Bar dataKey="Phones" fill={PRIMARY} radius={[5, 5, 0, 0]} maxBarSize={34} isAnimationActive={animate} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              {chipFamilyData.length > 0 && (
                <ChartCard title="Chipset families" subtitle="Most common chipset manufacturers" ariaLabel="Chipset family distribution">
                  <div className="donut-wrap">
                    <ResponsiveContainer width="100%" height={220}>
                      <PieChart>
                        <Tooltip content={<ChartTip />} />
                        <Pie data={chipFamilyData} dataKey="Phones" nameKey="name" innerRadius={62} outerRadius={92} paddingAngle={3} cornerRadius={6} stroke="none" isAnimationActive={animate}>
                          {chipFamilyData.map((entry, index) => (
                            <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="donut-center" aria-hidden="true">
                      <strong>{(data?.total_phones ?? 0).toLocaleString("en-IN")}</strong>
                      <small>phones</small>
                    </div>
                  </div>
                  <ul className="donut-legend">
                    {chipFamilyData.map((entry, index) => (
                      <li key={entry.name}>
                        <i style={{ background: PIE_COLORS[index % PIE_COLORS.length] }} />
                        {truncate(entry.name, 14)}
                      </li>
                    ))}
                  </ul>
                </ChartCard>
              )}
            </div>
          )}
        </div>
      </section>
    );
  }

  // Laptop insights (original)
  const priceData = data?.price_histogram?.map((d) => ({ name: d.bucket, Laptops: d.count })) ?? [];
  const brandData = data?.top_brands?.map((d) => ({ name: d.brand, Laptops: d.count })) ?? [];
  const purposeData = data?.purpose_distribution?.map((d) => ({ name: d.purpose, Laptops: d.count })) ?? [];
  const ramData = data?.ram_vs_price?.map((d) => ({ name: `${d.ram_gb} GB`, "Avg price": d.avg_price, Laptops: d.count })) ?? [];
  const tierData = data?.cpu_tier_distribution?.map((cpu, i) => ({ name: `Tier ${cpu.tier}`, CPU: cpu.count, GPU: data.gpu_tier_distribution[i]?.count ?? 0 })) ?? [];
  const storageData = data?.storage_type_distribution?.slice(0, 5)?.map((d) => ({ name: d.storage_type, Laptops: d.count })) ?? [];
  const horizontalHeight = Math.max(brandData.length, purposeData.length);

  return (
    <section id="insights" className="section insights">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">📊 Market Insights</span>
          <h2>The Nepali laptop market, visualized</h2>
          <p>Live charts built straight from our dataset of {(data?.total_laptops ?? 5284).toLocaleString("en-IN")} laptops — see where the market sits before you pick your machine.</p>
        </div>

        {error && !data && (
          <div className="insights__state" role="alert">
            <span className="insights__state-icon" aria-hidden="true">📉</span>
            <h3>Couldn&apos;t load the charts</h3>
            <p>{error}</p>
            <button type="button" className="btn btn-primary" onClick={handleRetry}>Try again</button>
          </div>
        )}

        {loading && !data && !error && (
          <div className="insights__grid" aria-hidden="true">
            <div className="skel-card skel-card--wide" />
            <div className="skel-card" />
            <div className="skel-card" />
            <div className="skel-card" />
            <div className="skel-card" />
          </div>
        )}

        {data && (
          <div className="insights__grid">
            <ChartCard wide title="Price landscape" subtitle="How many laptops fall into each NPR price band" ariaLabel="Histogram of laptop prices in Nepali rupees">
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={priceData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={PRIMARY} stopOpacity={0.35} />
                      <stop offset="100%" stopColor={PRIMARY} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_LINE} />
                  <XAxis dataKey="name" tick={AXIS_TICK} tickLine={false} axisLine={{ stroke: GRID_LINE }} interval={2} tickFormatter={(v) => v.endsWith("+") ? v : v.split("-")[0]} />
                  <YAxis allowDecimals={false} tick={AXIS_TICK} tickLine={false} axisLine={false} width={42} />
                  <Tooltip content={<ChartTip />} cursor={{ stroke: VIOLET, strokeDasharray: "4 4" }} />
                  <Area type="monotone" dataKey="Laptops" stroke={PRIMARY} strokeWidth={2.5} fill="url(#priceFill)" isAnimationActive={animate} />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Top brands" subtitle="Laptops in stock by brand" ariaLabel="Horizontal bar chart of the ten most common laptop brands">
              <ResponsiveContainer width="100%" height={horizontalHeight * 32 + 30}>
                <BarChart data={brandData} layout="vertical" margin={{ top: 0, right: 42, left: 0, bottom: 0 }}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" tick={{ ...AXIS_TICK, fontSize: 12 }} tickLine={false} axisLine={false} width={86} />
                  <Tooltip content={<ChartTip />} cursor={{ fill: "rgba(35,55,184,0.06)" }} />
                  <Bar dataKey="Laptops" fill={PRIMARY} radius={[0, 7, 7, 0]} barSize={16} isAnimationActive={animate}>
                    <LabelList dataKey="Laptops" position="right" style={{ fontSize: 11, fill: MUTED }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Built for every purpose" subtitle="Which use cases our dataset covers most" ariaLabel="Horizontal bar chart of laptop counts per purpose label">
              <ResponsiveContainer width="100%" height={horizontalHeight * 32 + 30}>
                <BarChart data={purposeData} layout="vertical" margin={{ top: 0, right: 42, left: 0, bottom: 0 }}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" tick={{ ...AXIS_TICK, fontSize: 12 }} tickFormatter={(v) => truncate(v)} tickLine={false} axisLine={false} width={128} />
                  <Tooltip content={<ChartTip />} cursor={{ fill: "rgba(124,58,237,0.06)" }} />
                  <Bar dataKey="Laptops" fill={VIOLET} radius={[0, 7, 7, 0]} barSize={16} isAnimationActive={animate}>
                    <LabelList dataKey="Laptops" position="right" style={{ fontSize: 11, fill: MUTED }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="More memory, more money" subtitle="Average price climbs with RAM size" ariaLabel="Bar chart of average laptop price for each RAM size">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={ramData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="ramFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={VIOLET} />
                      <stop offset="100%" stopColor="#a78bfa" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_LINE} />
                  <XAxis dataKey="name" tick={AXIS_TICK} tickLine={false} axisLine={{ stroke: GRID_LINE }} interval={1} />
                  <YAxis tickFormatter={fmtCompact} tick={AXIS_TICK} tickLine={false} axisLine={false} width={46} />
                  <Tooltip content={<ChartTip />} cursor={{ fill: "rgba(124,58,237,0.06)" }} />
                  <Bar dataKey="Avg price" fill="url(#ramFill)" radius={[7, 7, 0, 0]} maxBarSize={34} isAnimationActive={animate} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="CPU vs GPU power mix" subtitle="How laptops spread across our 1-6 performance tiers" ariaLabel="Grouped bar chart comparing CPU and GPU tier distribution">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={tierData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_LINE} />
                  <XAxis dataKey="name" tick={AXIS_TICK} tickLine={false} axisLine={{ stroke: GRID_LINE }} />
                  <YAxis allowDecimals={false} tick={AXIS_TICK} tickLine={false} axisLine={false} width={42} />
                  <Tooltip content={<ChartTip />} cursor={{ fill: "rgba(35,55,184,0.06)" }} />
                  <Bar dataKey="CPU" fill={PRIMARY} radius={[5, 5, 0, 0]} maxBarSize={26} isAnimationActive={animate} />
                  <Bar dataKey="GPU" fill={VIOLET} radius={[5, 5, 0, 0]} maxBarSize={26} isAnimationActive={animate} />
                </BarChart>
              </ResponsiveContainer>
              <div className="chart-legend" aria-hidden="true">
                <span><i style={{ background: PRIMARY }} /> CPU tiers</span>
                <span><i style={{ background: VIOLET }} /> GPU tiers</span>
              </div>
            </ChartCard>

            <ChartCard title="Storage types" subtitle="SSD rules the market — spinning disks are fading" ariaLabel="Donut chart of storage type distribution">
              <div className="donut-wrap">
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Tooltip content={<ChartTip />} />
                    <Pie data={storageData} dataKey="Laptops" nameKey="name" innerRadius={62} outerRadius={92} paddingAngle={3} cornerRadius={6} stroke="none" isAnimationActive={animate}>
                      {storageData.map((entry, index) => (
                        <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="donut-center" aria-hidden="true">
                  <strong>{(data?.total_laptops ?? 0).toLocaleString("en-IN")}</strong>
                  <small>laptops</small>
                </div>
              </div>
              <ul className="donut-legend">
                {storageData.map((entry, index) => (
                  <li key={entry.name}>
                    <i style={{ background: PIE_COLORS[index % PIE_COLORS.length] }} />
                    {truncate(entry.name, 14)}
                  </li>
                ))}
              </ul>
            </ChartCard>
          </div>
        )}
      </div>
    </section>
  );
}
