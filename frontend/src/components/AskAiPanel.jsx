import { useCallback, useEffect, useRef, useState } from "react";
import { streamAskAI } from "../services/api";
import { formatNpr } from "../data/options";
import "./AskAiPanel.css";

const BASE_SUGGESTIONS = [
  "Is this good value for the price?",
  "What is this laptop best for?",
  "Any downsides I should know?",
  "Suggest a cheaper alternative",
];

// Pick follow-up suggestions that match the laptop the user is viewing.
function suggestionsFor(laptop) {
  if (!laptop) return BASE_SUGGESTIONS;
  const purpose = String(laptop.purpose || "").toLowerCase();
  const cpu = String(laptop.cpu_model || "").toLowerCase();
  const gpu = String(laptop.gpu_model || "").toLowerCase();
  const price = Number(laptop.price_npr) || 0;

  const extra = [];
  if (purpose.includes("gaming") || gpu.includes("rtx") || gpu.includes("gtx")) {
    extra.push("How does it handle modern games?");
  }
  if (purpose.includes("video") || purpose.includes("edit") || cpu.includes("i7") || cpu.includes("i9") || cpu.includes("ryzen 7") || cpu.includes("ryzen 9")) {
    extra.push("Is this powerful enough for video editing?");
  }
  if (purpose.includes("student") || purpose.includes("study") || price < 50000) {
    extra.push("Is this a good pick for college work?");
  }
  if (purpose.includes("business") || purpose.includes("office")) {
    extra.push("How good is this for daily office work?");
  }
  return [...extra, ...BASE_SUGGESTIONS];
}

// Tiny markdown-lite renderer: turns **bold** and simple bullet/numbered
// lines into styled text. No HTML injection - builds React elements only.
function renderRichText(text) {
  const lines = String(text || "").split("\n");
  const blocks = [];
  let list = null;
  let listType = null;

  const flush = () => {
    if (list) blocks.push(list);
    list = null;
    listType = null;
  };

  const pushInline = (line) => {
    const parts = line.split(/(\*\*.+?\*\*)/g);
    return parts.map((part, i) =>
      part.startsWith("**") && part.endsWith("**") ? (
        <strong key={i}>{part.slice(2, -2)}</strong>
      ) : (
        <span key={i}>{part}</span>
      )
    );
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      flush();
      continue;
    }
    if (/^[-•*]\s+/.test(line)) {
      if (listType !== "ul" || !list) {
        flush();
        list = [];
        listType = "ul";
      }
      list.push(<li key={`${list.length}-${line}`}>{pushInline(line.replace(/^[-•*]\s+/, ""))}</li>);
    } else if (/^\d+[.)]\s+/.test(line)) {
      if (listType !== "ol" || !list) {
        flush();
        list = [];
        listType = "ol";
      }
      list.push(<li key={`${list.length}-${line}`}>{pushInline(line.replace(/^\d+[.)]\s+/, ""))}</li>);
    } else {
      flush();
      blocks.push(<p key={blocks.length}>{pushInline(line)}</p>);
    }
  }
  flush();
  return blocks;
}

export default function AskAiPanel({ rec, onViewLaptop }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const listRef = useRef(null);
  const inputRef = useRef(null);
  const abortRef = useRef(null);

  const laptop = rec.laptop;
  const suggestions = suggestionsFor(laptop);

  const scrollToEnd = useCallback(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, []);

  useEffect(() => {
    scrollToEnd();
  }, [messages, busy, scrollToEnd]);

  useEffect(() => {
    inputRef.current?.focus();
    return () => abortRef.current?.abort();
  }, []);

  // Friendlier message when Ollama/local model isn't reachable.
  const friendlyError = (msg) => {
    const m = String(msg || "");
    if (/ollama|model|server/i.test(m)) {
      return "The AI is offline — make sure Ollama is running, then hit Retry.";
    }
    return m || "Could not reach the AI service.";
  };

  const send = async (rawQuestion) => {
    const question = String(rawQuestion || "").trim();
    if (!question || busy) return;

    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", sources: null },
    ]);
    setInput("");
    setError(null);
    setBusy(true);

    const controller = new AbortController();
    abortRef.current = controller;

    const patchLast = (patch) =>
      setMessages((prev) => {
        const next = prev.slice();
        next[next.length - 1] = { ...next[next.length - 1], ...patch };
        return next;
      });

    try {
      let acc = "";
      let sources = null;
      const finalEvent = await streamAskAI(
        {
          question,
          history,
          top_n: 5,
          laptop,
        },
        (event) => {
          if (event.type === "start") {
            sources = Array.isArray(event.sources) ? event.sources : null;
            patchLast({ sources });
          } else if (event.type === "delta") {
            acc += event.text ?? "";
            patchLast({ content: acc });
          } else if (event.type === "done") {
            patchLast({
              content: (event.answer || acc).trim(),
              sources: Array.isArray(event.retrieved) ? event.retrieved : sources,
            });
          } else if (event.type === "error") {
            throw new Error(event.detail || "The AI could not finish its answer.");
          }
        },
        controller.signal
      );
      if (finalEvent?.type === "error" && !controller.signal.aborted) {
        setError(friendlyError(finalEvent.detail));
        patchLast({ content: "", failed: true });
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(friendlyError(err?.message));
        patchLast({
          content: "",
          failed: true,
        });
      }
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      send(input);
    }
  };

  const showSuggestions = messages.length === 0 && !busy;

  return (
    <section className="askai" aria-label="Ask AI about this laptop">
      <div className="askai__head">
        <span className="askai__title">🤖 Ask AI</span>
        <span className="askai__sub">answers grounded in our dataset</span>
      </div>

      <div className="askai__list" ref={listRef} role="log" aria-live="polite">
        {messages.length === 0 && (
          <p className="askai__intro">
            Hi! I can explain this laptop&apos;s specs, value for money and how it
            compares to others we stock. What would you like to know?
          </p>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`askai__msg askai__msg--${m.role}${m.failed ? " askai__msg--failed" : ""}`}>
            {m.role === "assistant" ? (
              <>
                {m.content === "" && busy && i === messages.length - 1 ? (
                  <span className="askai__thinking">
                    <span className="askai__typing" aria-label="AI is thinking">
                      <i /><i /><i />
                    </span>
                    {m.sources && m.sources.length > 0 && (
                      <span className="askai__grounded">reading {m.sources.length} dataset {m.sources.length === 1 ? "laptop" : "laptops"}…</span>
                    )}
                  </span>
                ) : (
                  <div className="askai__rich">{renderRichText(m.content)}</div>
                )}
                {m.sources && m.sources.length > 0 && m.content && (
                  <span className="askai__grounded">📚 grounded on {m.sources.length} dataset {m.sources.length === 1 ? "laptop" : "laptops"}</span>
                )}
              </>
            ) : (
              m.content || (m.failed ? "—" : "")
            )}
          </div>
        ))}

        {messages.filter((m) => m.role === "assistant").slice(-1)[0]?.sources?.length > 0 && (
          <div className="askai__citations" aria-label="Retrieved sources">
            {messages
              .filter((m) => m.role === "assistant" && m.sources?.length > 0)
              .slice(-1)[0]
              .sources.map((src) => (
                <button
                  key={src.rank}
                  type="button"
                  className="askai__cite"
                  onClick={() => onViewLaptop && onViewLaptop(src)}
                  title="Open this laptop's details"
                >
                  <span className="askai__cite-brand">{src.laptop.brand}</span>
                  <span className="askai__cite-name">{src.laptop.cpu_model}</span>
                  <span className="askai__cite-price">{formatNpr(src.laptop.price_npr)}</span>
                </button>
              ))}
          </div>
        )}
      </div>

      {showSuggestions && (
        <div className="askai__suggestions">
          {suggestions.map((s) => (
            <button key={s} type="button" className="askai__chip" onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="askai__error" role="alert">
          <span>{error}</span>
          <div className="askai__error-actions">
            <button type="button" onClick={() => send(messages.filter((m) => m.role === "user").slice(-1)[0]?.content)}>
              Retry
            </button>
            <button type="button" onClick={() => setError(null)}>Dismiss</button>
          </div>
        </div>
      )}

      <form
        className="askai__inputrow"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask about this laptop…"
          aria-label="Your question"
          maxLength={1000}
          disabled={busy}
        />
        <button type="submit" disabled={busy || !input.trim()} aria-label="Send question">
          Send
        </button>
      </form>
    </section>
  );
}