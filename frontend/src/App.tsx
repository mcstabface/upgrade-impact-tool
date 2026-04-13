import { useEffect, useState } from "react";
import { apiGet } from "./services/api";
import type { EnumCatalogResponse } from "./types/common";

function App() {
  const [catalog, setCatalog] = useState<EnumCatalogResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<EnumCatalogResponse>("/meta/enums")
      .then(setCatalog)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Upgrade Impact Analysis Tool</h1>
      <p>Phase 0 shell is alive.</p>

      {error && <p>API error: {error}</p>}

      {catalog && (
        <section>
          <h2>Enum Catalog</h2>
          <p>Analysis statuses: {catalog.analysis_statuses.join(", ")}</p>
          <p>Environment types: {catalog.environment_types.join(", ")}</p>
        </section>
      )}
    </main>
  );
}

export default App;