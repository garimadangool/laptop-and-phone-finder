import "./Hero.css";
import { useCountUp } from "../hooks/useCountUp";

export default function Hero({ stats, productType = "laptop" }) {
  const isPhone = productType === "phone";
  const total = isPhone
    ? (stats?.total_phones ?? 3328)
    : (stats?.total_laptops ?? 5284);
  const brands = stats ? Object.keys(stats.brands).length : (isPhone ? 20 : 27);
  const totalCount = useCountUp(total);
  const brandCount = useCountUp(brands);

  return (
    <section className="hero" id="home">
      <div className="container hero__inner">
        <div>
          <span className="hero__badge">⚡ Smart recommendations for Nepal</span>
          <h1>
            Find the {isPhone ? "phone" : "laptop"} that's{" "}
            <span className="hero__highlight">right for you.</span>
          </h1>
          <p>
            Tell us your budget and what you love doing — we scan{" "}
            {totalCount.toLocaleString("en-IN")} {isPhone ? "phones" : "laptops"}
            {" "}from top brands and hand-pick the best matches, with honest reasons
            why each one made the list.
          </p>

          <div className="hero__actions">
            <a className="btn btn-primary" href="#finder">
              Find My {isPhone ? "Phone" : "Laptop"} →
            </a>
            <a className="hero__secondary" href="#results">
              See how it works
            </a>
          </div>

          <dl className="hero__stats">
            <div>
              <dt>{totalCount.toLocaleString("en-IN")}</dt>
              <dd>{isPhone ? "Phones" : "Laptops"} analyzed</dd>
            </div>
            <div>
              <dt>{brandCount}</dt>
              <dd>Trusted brands</dd>
            </div>
            <div>
              <dt>NPR</dt>
              <dd>Prices in rupees</dd>
            </div>
          </dl>
        </div>

        <div className="hero__visual" aria-hidden="true">
          {isPhone ? (
            <>
              <div className="floaty floaty--1">📸 108MP Camera</div>
              <div className="floaty floaty--2">🎮 Flagship Chipset</div>
              <div className="floaty floaty--3">🔋 5000mAh Battery</div>

              <div className="hero__phone">
                <div className="hero__phone-notch" />
                <div className="hero__phone-screen">
                  <span className="chip chip--gold">🏆 Best Match 92%</span>
                  <span className="chip chip--blue">Snapdragon 8 Gen 3</span>
                  <span className="chip chip--green">256 GB</span>
                  <span className="chip chip--violet">Rs. 64,999</span>
                </div>
                <div className="hero__phone-bottom" />
              </div>
            </>
          ) : (
            <>
              <div className="floaty floaty--1">🎮 RTX Ready</div>
              <div className="floaty floaty--2">🎒 Student picks under 60K</div>
              <div className="floaty floaty--3">💻 16 GB RAM</div>

              <div className="hero__laptop">
                <div className="hero__laptop-screen">
                  <div className="hero__screen-top" />
                  <div className="hero__screen-body">
                    <span className="chip chip--gold">🏆 Best Match 94%</span>
                    <span className="chip chip--blue">Core i7</span>
                    <span className="chip chip--green">512 GB SSD</span>
                    <span className="chip chip--violet">Rs. 94,990</span>
                  </div>
                </div>
                <div className="hero__laptop-base" />
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
