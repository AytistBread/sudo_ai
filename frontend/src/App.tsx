import { FormEvent, useState } from "react";

type Verdict = "green" | "yellow" | "red";

type ParameterResult = {
  name: string;
  value: number | null;
  unit: string | null;
  allowed: string;
  status: Verdict;
};

type AnalyzeResponse = {
  verdict: Verdict;
  report_text: string;
  parameters: ParameterResult[];
  unmapped_params: string[];
  product_type: string;
};

const VERDICT_LABEL: Record<Verdict, string> = {
  green: "Годна",
  yellow: "Внимание",
  red: "Брак",
};

const API = "/api";

export default function App() {
  const [normsFile, setNormsFile] = useState<File | null>(null);
  const [protocolFile, setProtocolFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [coreLoaded, setCoreLoaded] = useState(false);

  async function ingest(event: FormEvent) {
    event.preventDefault();
    if (!normsFile) return;
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", normsFile);
      const response = await fetch(`${API}/criteria/ingest`, { method: "POST", body });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Не удалось загрузить нормативы");
      setCoreLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки CORE");
    } finally {
      setBusy(false);
    }
  }

  async function analyze(event: FormEvent) {
    event.preventDefault();
    if (!protocolFile) return;
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", protocolFile);
      const response = await fetch(`${API}/analyze`, { method: "POST", body });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Не удалось разобрать протокол");
      setResult(payload as AnalyzeResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка анализа");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <header className="top">
        <div>
          <p className="eyebrow">ООО Солярис</p>
          <h1>Выбраковка по протоколу лаборатории</h1>
        </div>
        <p className="hint">Агент фиксирует только факт соответствия. Причины и решения — у комиссии.</p>
      </header>

      <section className="panel">
        <form className="upload" onSubmit={ingest}>
          <label>
            Нормативы ГОСТ / ТУ
            <input type="file" accept=".xlsx,.xls,.csv" onChange={(e) => setNormsFile(e.target.files?.[0] ?? null)} />
          </label>
          <button type="submit" disabled={!normsFile || busy}>
            Сохранить CORE
          </button>
          {coreLoaded ? <span className="ok">CORE загружен</span> : null}
        </form>

        <form className="upload" onSubmit={analyze}>
          <label>
            Протокол испытаний
            <input type="file" accept=".xlsx,.xls,.csv" onChange={(e) => setProtocolFile(e.target.files?.[0] ?? null)} />
          </label>
          <button type="submit" disabled={!protocolFile || busy}>
            Проверить партию
          </button>
        </form>
      </section>

      {error ? <p className="error">{error}</p> : null}

      {result ? (
        <section className="result">
          <div className={`light ${result.verdict}`}>
            <span className="lamp" />
            <div>
              <strong>{VERDICT_LABEL[result.verdict]}</strong>
              <p>{result.product_type}</p>
            </div>
          </div>
          <pre className="report">{result.report_text}</pre>
          <table>
            <thead>
              <tr>
                <th>Параметр</th>
                <th>Факт</th>
                <th>Допуск</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {result.parameters.map((row) => (
                <tr key={row.name} className={row.status}>
                  <td>{row.name}</td>
                  <td>
                    {row.value ?? "—"} {row.unit ?? ""}
                  </td>
                  <td>{row.allowed}</td>
                  <td>{VERDICT_LABEL[row.status]}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {result.unmapped_params.length > 0 ? (
            <p className="hint">Не сопоставлено: {result.unmapped_params.join(", ")}</p>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}
