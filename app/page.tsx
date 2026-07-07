import fs from "node:fs";
import path from "node:path";

type FactorSet = {
  hr_pct: number;
  xbh_pct: number;
  single_pct: number;
  runs_pct: number;
};

type Game = {
  game_id: string;
  start_time_local: string;
  away_team: string;
  home_team: string;
  stadium: { id: string; name_ko: string; city: string | null; type: string };
  weather: null | {
    label: string;
    temperature_c: number;
    humidity_pct: number;
    pressure_hpa: number;
    precipitation_probability_pct: number;
    wind_speed_mps: number;
    wind_direction_deg: number;
  };
  factors: {
    stadium_only: FactorSet;
    weather_only: FactorSet;
    combined: FactorSet;
  };
  explanations: string[];
  data_status: string;
};

type DailyArtifact = {
  date: string;
  generated_at: string;
  warnings: string[];
  games: Game[];
};

const views = [
  ["combined", "통합 효과"],
  ["stadium_only", "구장만"],
  ["weather_only", "날씨만"]
] as const;

type ViewKey = (typeof views)[number][0];

function loadArtifact(): DailyArtifact {
  const filePath = path.join(process.cwd(), "data", "daily-factors", "2026-07-07.json");
  return JSON.parse(fs.readFileSync(filePath, "utf-8")) as DailyArtifact;
}

function formatPct(value: number) {
  if (value > 0) return `+${value}%`;
  return `${value}%`;
}

function valueClass(value: number) {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

export default async function Home({
  searchParams
}: {
  searchParams: Promise<{ view?: string }>;
}) {
  const params = await searchParams;
  const requestedView = params.view;
  const view: ViewKey = requestedView === "stadium_only" || requestedView === "weather_only" ? requestedView : "combined";
  const artifact = loadArtifact();

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">KBO PARK FACTORS</p>
          <h1>{artifact.date}</h1>
          <p className="updated">Last updated {new Date(artifact.generated_at).toLocaleString("ko-KR")}</p>
        </div>
        <nav className="segments" aria-label="factor view">
          {views.map(([key, label]) => (
            <a className={view === key ? "active" : ""} href={`/?view=${key}`} key={key}>
              {label}
            </a>
          ))}
        </nav>
      </header>

      {artifact.warnings.length > 0 ? (
        <section className="warning">{artifact.warnings.join(" · ")}</section>
      ) : null}

      <section className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>Game</th>
              <th>Weather</th>
              <th>HR</th>
              <th>2B/3B</th>
              <th>1B</th>
              <th>Runs</th>
            </tr>
          </thead>
          <tbody>
            {artifact.games.map((game) => {
              const factors = game.factors[view];
              return (
                <tr key={game.game_id}>
                  <td>
                    <strong>
                      {game.away_team} @ {game.home_team}
                    </strong>
                    <span>
                      {game.stadium.name_ko} · {game.start_time_local}
                    </span>
                    <small>{game.explanations[0]}</small>
                  </td>
                  <td>
                    {game.weather ? (
                      <span>
                        {game.weather.label} · {Math.round(game.weather.temperature_c)}°C · {game.weather.wind_speed_mps}m/s
                      </span>
                    ) : (
                      <span>{game.stadium.type === "dome" ? "돔/날씨 제한" : "날씨 미확보"}</span>
                    )}
                  </td>
                  <td className={valueClass(factors.hr_pct)}>{formatPct(factors.hr_pct)}</td>
                  <td className={valueClass(factors.xbh_pct)}>{formatPct(factors.xbh_pct)}</td>
                  <td className={valueClass(factors.single_pct)}>{formatPct(factors.single_pct)}</td>
                  <td className={valueClass(factors.runs_pct)}>{formatPct(factors.runs_pct)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </main>
  );
}
