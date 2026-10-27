import "./Footer.css";

export default function Footer() {
  return (
    <footer className="footer" id="about">
      <div className="container footer__inner">
        <div>
          <p className="footer__logo">
            Laptop<em>Finder</em>
            <small>.np</small>
          </p>
          <p className="footer__tagline">
            Smart laptop recommendations for Nepali students, gamers and
            professionals — powered by a scoring engine trained on{" "}
            5,284+ real laptops.
          </p>
        </div>

        <nav className="footer__links" aria-label="Footer">
          <a href="#home">Home</a>
          <a href="#finder">Find Laptop</a>
          <a href="#results">Recommendations</a>
          <a href="#insights">Market Insights</a>
        </nav>

        <p className="footer__meta">
          🤖 Ask AI live on every product · Built with React + FastAPI · Prices in NPR
        </p>
      </div>
    </footer>
  );
}
