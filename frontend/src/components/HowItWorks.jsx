import "./HowItWorks.css";

const LAPTOP_STEPS = [
  {
    num: "1",
    icon: "🗣️",
    title: "Tell us your needs",
    body: "Pick your purpose (mixing several is fine) and set a budget in NPR. Add must-haves like RAM or brand if you like — everything else is optional.",
  },
  {
    num: "2",
    icon: "🧠",
    title: "We scan the catalogue",
    body: "Our scoring engine grades each of 5,284 laptops on budget fit, purpose fit, raw specs and balance — then ranks the best matches for you.",
  },
  {
    num: "3",
    icon: "🛍️",
    title: "Compare & decide",
    body: "Review honest reasons why each laptop made the list, compare up to 4 side-by-side, and ask the AI assistant anything before you decide.",
  },
];

const PHONE_STEPS = [
  {
    num: "1",
    icon: "🗣️",
    title: "Tell us your needs",
    body: "Pick what you'll use it for (gaming, camera, student, etc.) and set a budget in NPR. Optional: filter by brand, chipset tier, RAM, or must-have features like 5G.",
  },
  {
    num: "2",
    icon: "🧠",
    title: "We scan the catalogue",
    body: "Our engine scores each of 3,328 phones on budget fit, purpose fit, chipset power, camera, battery and connectivity — then ranks the best matches.",
  },
  {
    num: "3",
    icon: "🛍️",
    title: "Compare & decide",
    body: "Review why each phone made the list, compare up to 4 side-by-side, and check detailed specs before you decide.",
  },
];

export default function HowItWorks({ productType = "laptop" }) {
  const steps = productType === "phone" ? PHONE_STEPS : LAPTOP_STEPS;
  const isPhone = productType === "phone";

  return (
    <section className="section how" id="how">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">🧭 How it works</span>
          <h2>Three steps to your perfect {isPhone ? "phone" : "laptop"}.</h2>
          <p>No spec-sheet degree needed — we do the heavy lifting.</p>
        </div>

        <ol className="how__steps">
          {steps.map((step) => (
            <li key={step.num} className="how__step">
              <span className="how__step-num" aria-hidden="true">
                {step.num}
              </span>
              <span className="how__step-icon" aria-hidden="true">
                {step.icon}
              </span>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </li>
          ))}
        </ol>

        <div className="how__cta">
          <a className="btn btn-primary" href="#finder">
            Get Started →
          </a>
        </div>
      </div>
    </section>
  );
}
