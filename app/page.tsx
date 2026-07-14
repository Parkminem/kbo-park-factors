import fs from "node:fs";
import path from "node:path";
import { dailyArtifacts, validationArtifacts } from "./generated-data";

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
  stadium: {
    id: string;
    name_ko: string;
    city: string | null;
    type: string;
    orientation_deg?: number;
    baseline_evidence?: null | {
      games: number;
      prior_games: number;
      raw_factors: FactorSet;
      adjusted_factors: FactorSet;
    };
  };
  weather: null | {
    label: string;
    temperature_c: number;
    humidity_pct: number;
    pressure_hpa: number;
    precipitation_probability_pct: number;
    weather_code: number;
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

type ValidationArtifact = {
  date: string;
  generated_at: string;
  summary: {
    predicted_games: number;
    completed_games: number;
    pending_games: number;
    total_home_runs: number;
    total_runs: number;
    avg_predicted_hr_pct: number | null;
    avg_predicted_runs_pct: number | null;
  };
};

type CalibrationSummary = {
  completed_days: number;
  baseline_home_runs_per_game: number | null;
  baseline_runs_per_game: number | null;
  hr_mae_pct: number | null;
  runs_mae_pct: number | null;
};

type ValidationHistory = {
  summary: ValidationArtifact["summary"] & {
    days: number;
    calibration: CalibrationSummary;
  };
  recentDays: ValidationArtifact[];
};

const views = [
  ["combined", "Combined Effect"],
  ["stadium_only", "Stadium Only"],
  ["weather_only", "Weather Only"]
] as const;

type ViewKey = (typeof views)[number][0];

export const dynamic = "force-dynamic";

const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

function todayInSeoul(now = new Date()): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).formatToParts(now);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function resolveDate(value: string | undefined, fallbackDate: string): string | null {
  if (value === undefined) return fallbackDate;
  return DATE_PATTERN.test(value) ? value : null;
}

function loadArtifact(date: string): DailyArtifact | null {
  const bundled = (dailyArtifacts as Record<string, DailyArtifact>)[date];
  if (bundled) return bundled;

  try {
    const filePath = path.join(process.cwd(), "data", "daily-factors", `${date}.json`);
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as DailyArtifact;
  } catch {
    return null;
  }
}

function loadValidation(date: string): ValidationArtifact | null {
  const bundled = (validationArtifacts as Record<string, ValidationArtifact>)[date];
  if (bundled) return bundled;

  try {
    const filePath = path.join(process.cwd(), "data", "validations", `${date}.json`);
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as ValidationArtifact;
  } catch {
    return null;
  }
}

function loadValidationHistory(limit = 7): ValidationHistory | null {
  try {
    const bundledValidations = Object.values(validationArtifacts as Record<string, ValidationArtifact>);
    const validations =
      bundledValidations.length > 0
        ? bundledValidations.sort((a, b) => b.date.localeCompare(a.date))
        : fs
            .readdirSync(path.join(process.cwd(), "data", "validations"))
            .filter((fileName) => fileName.endsWith(".json"))
            .map((fileName) => JSON.parse(fs.readFileSync(path.join(process.cwd(), "data", "validations", fileName), "utf-8")) as ValidationArtifact)
            .sort((a, b) => b.date.localeCompare(a.date));

    if (validations.length === 0) return null;

    const summary = validations.reduce(
      (acc, validation) => {
        const item = validation.summary;
        acc.days += 1;
        acc.predicted_games += item.predicted_games;
        acc.completed_games += item.completed_games;
        acc.pending_games += item.pending_games;
        acc.total_home_runs += item.total_home_runs;
        acc.total_runs += item.total_runs;
        if (item.avg_predicted_hr_pct !== null && item.predicted_games > 0) {
          acc.weightedHr += item.avg_predicted_hr_pct * item.predicted_games;
          acc.hrWeight += item.predicted_games;
        }
        if (item.avg_predicted_runs_pct !== null && item.predicted_games > 0) {
          acc.weightedRuns += item.avg_predicted_runs_pct * item.predicted_games;
          acc.runsWeight += item.predicted_games;
        }
        return acc;
      },
      {
        days: 0,
        predicted_games: 0,
        completed_games: 0,
        pending_games: 0,
        total_home_runs: 0,
        total_runs: 0,
        weightedHr: 0,
        hrWeight: 0,
        weightedRuns: 0,
        runsWeight: 0
      }
    );

    return {
      summary: {
        days: summary.days,
        predicted_games: summary.predicted_games,
        completed_games: summary.completed_games,
        pending_games: summary.pending_games,
        total_home_runs: summary.total_home_runs,
        total_runs: summary.total_runs,
        avg_predicted_hr_pct: summary.hrWeight === 0 ? null : Math.round(summary.weightedHr / summary.hrWeight),
        avg_predicted_runs_pct: summary.runsWeight === 0 ? null : Math.round(summary.weightedRuns / summary.runsWeight),
        calibration: summarizeCalibration(validations)
      },
      recentDays: validations.slice(0, limit)
    };
  } catch {
    return null;
  }
}

function summarizeCalibration(validations: ValidationArtifact[]): CalibrationSummary {
  const completed = validations.filter((validation) => validation.summary.completed_games > 0);
  const completedGames = completed.reduce((total, validation) => total + validation.summary.completed_games, 0);
  const totalHomeRuns = completed.reduce((total, validation) => total + validation.summary.total_home_runs, 0);
  const totalRuns = completed.reduce((total, validation) => total + validation.summary.total_runs, 0);

  if (completedGames === 0) {
    return {
      completed_days: 0,
      baseline_home_runs_per_game: null,
      baseline_runs_per_game: null,
      hr_mae_pct: null,
      runs_mae_pct: null
    };
  }

  const baselineHomeRunsPerGame = totalHomeRuns / completedGames;
  const baselineRunsPerGame = totalRuns / completedGames;
  return {
    completed_days: completed.length,
    baseline_home_runs_per_game: roundToTwo(baselineHomeRunsPerGame),
    baseline_runs_per_game: roundToTwo(baselineRunsPerGame),
    hr_mae_pct: calibrationMae(completed, "avg_predicted_hr_pct", "total_home_runs", baselineHomeRunsPerGame),
    runs_mae_pct: calibrationMae(completed, "avg_predicted_runs_pct", "total_runs", baselineRunsPerGame)
  };
}

function calibrationMae(
  validations: ValidationArtifact[],
  predictionKey: "avg_predicted_hr_pct" | "avg_predicted_runs_pct",
  actualTotalKey: "total_home_runs" | "total_runs",
  baselinePerGame: number
) {
  if (baselinePerGame <= 0) return null;

  let weightedError = 0;
  let totalWeight = 0;
  for (const validation of validations) {
    const prediction = validation.summary[predictionKey];
    const completedGames = validation.summary.completed_games;
    if (prediction === null || completedGames === 0) continue;
    const actualPerGame = validation.summary[actualTotalKey] / completedGames;
    const actualPct = (actualPerGame / baselinePerGame - 1) * 100;
    weightedError += Math.abs(prediction - actualPct) * completedGames;
    totalWeight += completedGames;
  }

  return totalWeight === 0 ? null : Math.round(weightedError / totalWeight);
}

function roundToTwo(value: number) {
  return Math.round(value * 100) / 100;
}

function viewHref(view: ViewKey, showAll: boolean) {
  const query = new URLSearchParams({ view });
  if (showAll) query.set("show", "all");
  return `/?${query.toString()}`;
}

function modeHref(view: ViewKey, showAll: boolean) {
  const query = new URLSearchParams({ view });
  if (showAll) query.set("show", "all");
  return `/?${query.toString()}`;
}

function formatPct(value: number) {
  if (value > 0) return `+${value}%`;
  return `${value}%`;
}

function formatNullablePct(value: number | null) {
  return value === null ? "-" : formatPct(value);
}

function formatNullableNumber(value: number | null, digits = 2) {
  return value === null ? "-" : value.toFixed(digits);
}

function valueClass(value: number) {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function compassPoint(degrees: number) {
  const labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
  return labels[Math.round((((degrees % 360) + 360) % 360) / 22.5) % 16];
}

function weatherTone(game: Game) {
  if (!game.weather) return "neutralWeather";
  if (game.weather.precipitation_probability_pct >= 50) return "rainWeather";
  if (game.weather.temperature_c >= 30) return "hotWeather";
  if (game.weather.weather_code <= 1) return "clearWeather";
  return "cloudWeather";
}

function windImpact(game: Game) {
  if (!game.weather || game.stadium.type === "dome") {
    return { label: "DOME", detail: "날씨 영향 없음", className: "neutralImpact" };
  }
  const orientation = game.stadium.orientation_deg ?? 45;
  const windTo = (game.weather.wind_direction_deg + 180) % 360;
  const diff = Math.abs((((windTo - orientation + 540) % 360) - 180));
  if (diff <= 35) return { label: "OUT", detail: "외야 방향", className: "boostImpact" };
  if (diff >= 145) return { label: "IN", detail: "홈 방향", className: "dragImpact" };
  return { label: "CROSS", detail: diff < 90 ? "대각 외야" : "대각 홈", className: "neutralImpact" };
}

function WeatherMark({ game }: { game: Game }) {
  const precip = game.weather?.precipitation_probability_pct ?? 0;
  if (!game.weather) {
    return (
      <svg className="weatherMark" viewBox="0 0 48 48" aria-hidden="true">
        <path d="M15 31h18a9 9 0 0 0-1-18 13 13 0 0 0-24 7 7 7 0 0 0 7 11z" fill="none" stroke="currentColor" strokeWidth="4" />
      </svg>
    );
  }
  if (precip >= 50) {
    return (
      <svg className="weatherMark" viewBox="0 0 48 48" aria-hidden="true">
        <path d="M15 27h18a8 8 0 0 0-1-16 12 12 0 0 0-23 6 6 6 0 0 0 6 10z" fill="none" stroke="currentColor" strokeWidth="4" />
        <path d="M17 34l-3 7M27 34l-3 7M37 34l-3 7" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
      </svg>
    );
  }
  if (game.weather.weather_code <= 1) {
    return (
      <svg className="weatherMark" viewBox="0 0 48 48" aria-hidden="true">
        <circle cx="24" cy="24" r="9" fill="none" stroke="currentColor" strokeWidth="4" />
        <path d="M24 4v7M24 37v7M4 24h7M37 24h7M10 10l5 5M33 33l5 5M38 10l-5 5M15 33l-5 5" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg className="weatherMark" viewBox="0 0 48 48" aria-hidden="true">
      <path d="M15 31h18a9 9 0 0 0-1-18 13 13 0 0 0-24 7 7 7 0 0 0 7 11z" fill="none" stroke="currentColor" strokeWidth="4" />
    </svg>
  );
}

function BallparkWind({ game }: { game: Game }) {
  const orientation = game.stadium.orientation_deg ?? 45;
  const windFrom = game.weather?.wind_direction_deg ?? orientation;
  const windTo = (windFrom + 180) % 360;
  const relativeWindTo = windTo - orientation;
  const hasWeather = game.weather !== null && game.stadium.type !== "dome";

  return (
    <svg className="parkDiagram" viewBox="0 0 180 142" role="img" aria-label={`${game.stadium.name_ko} wind direction`}>
      <path className="stadiumShell" d="M18 118C18 57 45 20 90 9c45 11 72 48 72 109H18z" />
      <path className="outfield" d="M28 113C28 61 51 29 90 19c39 10 62 42 62 94H28z" />
      <path className="grassStripe stripeLeft" d="M42 110C44 72 58 47 90 28" />
      <path className="grassStripe stripeRight" d="M138 110C136 72 122 47 90 28" />
      <path className="foulLine" d="M90 113L38 58M90 113l52-55" />
      <path className="infieldDirt" d="M90 113L61 84l29-29 29 29-29 29z" />
      <path className="moundArc" d="M71 83a19 19 0 0 1 38 0" />
      <circle className="base" cx="67" cy="84" r="3" />
      <circle className="base" cx="90" cy="61" r="3" />
      <circle className="base" cx="113" cy="84" r="3" />
      <path className="homePlate" d="M85 113h10l3 5-8 6-8-6z" />
      {hasWeather ? (
        <g className="windVector" transform={`rotate(${relativeWindTo} 90 84)`}>
          <path className="windVectorGlow" d="M90 105V70" />
          <path className="windVectorLine" d="M90 105V70" />
          <path className="windVectorHead" d="M90 57l-13 20 13-6 13 6z" />
        </g>
      ) : (
        <g className="domeMark">
          <path d="M60 80c13-22 47-22 60 0" />
          <path d="M67 90h46" />
        </g>
      )}
    </svg>
  );
}

function WeatherSummary({ game }: { game: Game }) {
  if (!game.weather) {
    return (
      <div className="weatherLine">
        <WeatherMark game={game} />
        <strong>Dome</strong>
        <span>weather neutral</span>
      </div>
    );
  }
  return (
    <div className="weatherLine">
      <WeatherMark game={game} />
      <strong>{Math.round(game.weather.temperature_c)}°</strong>
      <span>{game.weather.precipitation_probability_pct}% rain</span>
      <span>{compassPoint(game.weather.wind_direction_deg)} {game.weather.wind_speed_mps.toFixed(1)} m/s</span>
    </div>
  );
}

function FactorEvidence({ game, factors }: { game: Game; factors: FactorSet }) {
  const evidence = game.stadium.baseline_evidence;
  return (
    <details className="evidencePanel">
      <summary>근거 보기</summary>
      <div className="evidenceBody">
        <div className="evidenceGrid">
          <div>
            <span>HR</span>
            <strong className={valueClass(factors.hr_pct)}>{formatPct(factors.hr_pct)}</strong>
            <small>
              구장 {formatPct(game.factors.stadium_only.hr_pct)} · 날씨 {formatPct(game.factors.weather_only.hr_pct)}
            </small>
          </div>
          <div>
            <span>Runs</span>
            <strong className={valueClass(factors.runs_pct)}>{formatPct(factors.runs_pct)}</strong>
            <small>
              구장 {formatPct(game.factors.stadium_only.runs_pct)} · 날씨 {formatPct(game.factors.weather_only.runs_pct)}
            </small>
          </div>
        </div>
        {evidence ? (
          <p>
            구장 기준값은 KBO 공식 GameCenter {evidence.games}경기 raw HR {formatPct(evidence.raw_factors.hr_pct)}, Runs{" "}
            {formatPct(evidence.raw_factors.runs_pct)}를 {evidence.prior_games}경기 prior로 평균회귀해 HR{" "}
            {formatPct(evidence.adjusted_factors.hr_pct)}, Runs {formatPct(evidence.adjusted_factors.runs_pct)}로 사용합니다.
          </p>
        ) : (
          <p>구장 기준값 근거 메타데이터가 없는 행입니다.</p>
        )}
        {game.weather ? (
          <p>
            날씨는 {Math.round(game.weather.temperature_c)}도, {game.weather.precipitation_probability_pct}% rain,{" "}
            {compassPoint(game.weather.wind_direction_deg)} {game.weather.wind_speed_mps.toFixed(1)} m/s를 반영합니다.
          </p>
        ) : (
          <p>{game.stadium.type === "dome" ? "돔 구장이라 외부 날씨 영향은 0으로 처리합니다." : "날씨 데이터가 없어 구장 기준값만 반영합니다."}</p>
        )}
        <ul>
          {game.explanations.map((explanation) => (
            <li key={explanation}>{explanation}</li>
          ))}
        </ul>
      </div>
    </details>
  );
}

function ValidationSummary({ validation }: { validation: ValidationArtifact }) {
  const summary = validation.summary;
  return (
    <section className="validationCard" aria-label="validation summary">
      <div>
        <span>검증 결과</span>
        <strong>{summary.completed_games}/{summary.predicted_games}</strong>
        <small>완료 경기 · Last checked {new Date(validation.generated_at).toLocaleString("ko-KR")}</small>
      </div>
      <div>
        <span>Pending</span>
        <strong>{summary.pending_games}</strong>
        <small>공식 결과 대기</small>
      </div>
      <div>
        <span>Actual HR</span>
        <strong>{summary.total_home_runs}</strong>
        <small>완료 경기 합계</small>
      </div>
      <div>
        <span>Actual Runs</span>
        <strong>{summary.total_runs}</strong>
        <small>완료 경기 합계</small>
      </div>
      <div>
        <span>Avg Pred HR</span>
        <strong>{formatNullablePct(summary.avg_predicted_hr_pct)}</strong>
        <small>Combined 평균</small>
      </div>
      <div>
        <span>Avg Pred Runs</span>
        <strong>{formatNullablePct(summary.avg_predicted_runs_pct)}</strong>
        <small>Combined 평균</small>
      </div>
    </section>
  );
}

function ValidationHistoryCard({ history }: { history: ValidationHistory }) {
  const summary = history.summary;
  const calibration = summary.calibration;
  return (
    <details className="historyCard" aria-label="validation history">
      <summary className="historyTabSummary">
        <div className="historyTabTitle">
          <span>검증 히스토리</span>
          <strong>{summary.days}일 누적</strong>
        </div>
        <div className="historyPreviewMetrics">
          <span>
            <small>Done</small>
            <strong>{summary.completed_games}/{summary.predicted_games}</strong>
          </span>
          <span>
            <small>HR Error</small>
            <strong>{formatNullablePct(calibration.hr_mae_pct)}</strong>
          </span>
          <span>
            <small>Runs Error</small>
            <strong>{formatNullablePct(calibration.runs_mae_pct)}</strong>
          </span>
        </div>
        <span className="historyOpenCue" aria-hidden="true" />
      </summary>
      <div className="historyPanel">
        <div className="historyHeader">
          <p>
            완료 {summary.completed_games}/{summary.predicted_games}경기 · HR {summary.total_home_runs} · Runs {summary.total_runs}
          </p>
        </div>
        <div className="historyStats">
          <div>
            <span>Pending</span>
            <strong>{summary.pending_games}</strong>
          </div>
          <div>
            <span>Avg Pred HR</span>
            <strong>{formatNullablePct(summary.avg_predicted_hr_pct)}</strong>
          </div>
          <div>
            <span>Avg Pred Runs</span>
            <strong>{formatNullablePct(summary.avg_predicted_runs_pct)}</strong>
          </div>
        </div>
        <div className="calibrationStrip" aria-label="calibration metrics">
          <div>
            <span>HR Error</span>
            <strong>{formatNullablePct(calibration.hr_mae_pct)}</strong>
            <small>예측 vs 실제 기준 대비 오차</small>
          </div>
          <div>
            <span>Runs Error</span>
            <strong>{formatNullablePct(calibration.runs_mae_pct)}</strong>
            <small>예측 vs 실제 기준 대비 오차</small>
          </div>
          <div>
            <span>Actual Baseline</span>
            <strong>
              {formatNullableNumber(calibration.baseline_home_runs_per_game, 2)} HR · {formatNullableNumber(calibration.baseline_runs_per_game, 1)} R
            </strong>
            <small>{calibration.completed_days}일 완료 경기 기준</small>
          </div>
        </div>
        <div className="historyTable" role="table" aria-label="recent validation days">
          <div className="historyTableHead" role="row">
            <span role="columnheader">Date</span>
            <span role="columnheader">Done</span>
            <span role="columnheader">HR</span>
            <span role="columnheader">Runs</span>
            <span role="columnheader">Pred HR</span>
            <span role="columnheader">Pred Runs</span>
          </div>
          {history.recentDays.map((day) => (
            <div className="historyTableRow" role="row" key={day.date}>
              <span role="cell">{day.date}</span>
              <span role="cell">
                {day.summary.completed_games}/{day.summary.predicted_games}
              </span>
              <span role="cell">{day.summary.total_home_runs}</span>
              <span role="cell">{day.summary.total_runs}</span>
              <span role="cell">{formatNullablePct(day.summary.avg_predicted_hr_pct)}</span>
              <span role="cell">{formatNullablePct(day.summary.avg_predicted_runs_pct)}</span>
            </div>
          ))}
        </div>
      </div>
    </details>
  );
}

export default async function Home({
  searchParams
}: {
  searchParams: Promise<{ view?: string; date?: string; show?: string }>;
}) {
  const params = await searchParams;
  const requestedView = params.view;
  const view: ViewKey = requestedView === "stadium_only" || requestedView === "weather_only" ? requestedView : "combined";
  const showAll = params.show === "all";
  const defaultDate = todayInSeoul();
  const selectedDate = resolveDate(params.date, defaultDate);
  const artifact = selectedDate === null ? null : loadArtifact(selectedDate);
  const validation = selectedDate === null ? null : loadValidation(selectedDate);
  const validationHistory = loadValidationHistory();
  const displayDate = artifact?.date ?? selectedDate ?? params.date ?? defaultDate;
  const visibleGames = artifact?.games.filter((game) => showAll || !game.data_status.startsWith("stadium_reference")) ?? [];

  return (
    <main className="page">
      <header className="topbar">
        <div className="brandBlock">
          <a className="brandLink" href="/" aria-label="Korea Baseball Park Factors home">
            <span className="brandMark" aria-hidden="true">
              <span className="brandDiamond" />
              <span className="brandSun" />
            </span>
            <span className="brandText">
              <span className="eyebrow">Korea Baseball Park Factors</span>
              <span>Park + Weather Edge</span>
            </span>
          </a>
          <h1>{displayDate}</h1>
          {artifact ? <p className="updated">Last updated {new Date(artifact.generated_at).toLocaleString("ko-KR")}</p> : null}
        </div>
        <nav className="segments" aria-label="factor view">
          {views.map(([key, label]) => (
            <a className={view === key ? "active" : ""} href={viewHref(key, showAll)} key={key}>
              {label}
            </a>
          ))}
        </nav>
      </header>

      {artifact ? (
        <nav className="displayToggle" aria-label="display mode">
          <a className={!showAll ? "active" : ""} href={modeHref(view, false)}>경기만</a>
          <a className={showAll ? "active" : ""} href={modeHref(view, true)}>전체 구장</a>
        </nav>
      ) : null}

      {!artifact ? (
        <section className="warning">
          No park-factor data is available for {displayDate}. The daily artifact may not have been generated yet.
        </section>
      ) : null}

      {artifact && artifact.warnings.length > 0 ? (
        <section className="warning">{artifact.warnings.join(" · ")}</section>
      ) : null}

      {validation ? <ValidationSummary validation={validation} /> : null}
      {validationHistory ? <ValidationHistoryCard history={validationHistory} /> : null}

      {artifact && visibleGames.length === 0 ? (
        <section className="emptyState">
          <strong>오늘 예정된 KBO 경기가 없습니다.</strong>
          <span>구장별 기준값과 날씨 환경은 전체 구장 보기에서 확인할 수 있습니다.</span>
          <a href={modeHref(view, true)}>전체 구장 보기</a>
        </section>
      ) : null}

      {artifact && visibleGames.length > 0 ? (
        <section className="gameGrid">
          {visibleGames.map((game) => {
            const factors = game.factors[view];
            const isReference = game.data_status.startsWith("stadium_reference");
            const impact = windImpact(game);
            return (
              <article className={`weatherRow ${weatherTone(game)}`} key={game.game_id}>
                <div className="matchBlock">
                  <div className="matchText">
                    <strong>{isReference ? game.stadium.name_ko : `${game.away_team} @ ${game.home_team}`}</strong>
                    <span>
                      {isReference ? "경기 없음" : game.stadium.name_ko} · {game.start_time_local}
                    </span>
                  </div>
                </div>

                <div className="parkBlock">
                  <BallparkWind game={game} />
                </div>

                <div className="conditionBlock">
                  <div className={`impactBadge ${impact.className}`}>
                    <strong>{impact.label}</strong>
                    <span>{impact.detail}</span>
                  </div>
                  <WeatherSummary game={game} />
                </div>

                <div className="factorBlock">
                  <div>
                    <span>HR</span>
                    <strong className={valueClass(factors.hr_pct)}>{formatPct(factors.hr_pct)}</strong>
                  </div>
                  <div>
                    <span>Runs</span>
                    <strong className={valueClass(factors.runs_pct)}>{formatPct(factors.runs_pct)}</strong>
                  </div>
                </div>

                <FactorEvidence game={game} factors={factors} />
              </article>
            );
          })}
        </section>
      ) : null}

      <footer className="siteFooter">
        <div>
          <a className="footerBrand" href="/" aria-label="Korea Baseball Park Factors home">
            <span className="footerMark" aria-hidden="true" />
            <span>Korea Baseball Park Factors</span>
          </a>
          <p>Stadium and weather context for daily Korea baseball run environments.</p>
          <p className="footerNotice">Unofficial analytics project. Not affiliated with or endorsed by KBO or its clubs.</p>
        </div>
        <div className="footerMeta">
          <span>{artifact ? `Updated ${new Date(artifact.generated_at).toLocaleString("ko-KR")}` : `No data for ${displayDate}`}</span>
          <span>{visibleGames.length} rows shown</span>
          <span>Official records · Weather model inputs</span>
        </div>
      </footer>
    </main>
  );
}
