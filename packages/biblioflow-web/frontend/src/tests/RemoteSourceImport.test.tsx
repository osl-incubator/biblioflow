import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { App } from "../App";

interface MockResponseInit {
  status?: number;
  ok?: boolean;
}

function jsonResponse(payload: unknown, init: MockResponseInit = {}): Response {
  return {
    ok: init.ok ?? (init.status ?? 200) < 400,
    status: init.status ?? 200,
    json: () => Promise.resolve(payload),
  } as Response;
}

function renderProjectUpload() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/projects/project-1/upload"]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function renderProjectScreening(runId = "search-1", query?: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const screeningQuery = query ?? `run=${runId}`;
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter
        initialEntries={[`/projects/project-1/screening?${screeningQuery}`]}
      >
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("remote source import", () => {
  it("shows a not found state when the project cannot be loaded", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(
        jsonResponse(
          { error: { message: "Project not found" } },
          { status: 404 },
        ),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    expect(await screen.findByText("Project not found")).toBeDefined();
    expect(
      screen.getByRole("link", { name: /Back to projects/i }),
    ).toBeDefined();
  });

  it("stages a PMC search, records a keep decision, and promotes selected candidates", async () => {
    const searchBodies: unknown[] = [];
    const decisionBodies: unknown[] = [];
    const promoteBodies: unknown[] = [];
    let activeDatasetId: string | null = null;
    const stagedSearch = {
      screening_run_id: "search-1",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      source: "pmc",
      source_label: "PubMed Central",
      query: "open science",
      limit: 12,
      name: "PMC import",
      records: 2,
      status_counts: { candidate: 2 },
      candidates: [
        {
          candidate_id: "candidate-1",
          status: "candidate",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          record: { title: "PMC record", pmcid: "PMC1" },
          identifiers: { pmcid: "PMC1", doi: "10.1234/pmc" },
          title: "PMC record",
          year: 2025,
          authors: ["Grace Hopper"],
          source_title: "Open Full Text Research",
        },
        {
          candidate_id: "candidate-2",
          status: "candidate",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          record: { title: "Excluded record", pmcid: "PMC2" },
          identifiers: { pmcid: "PMC2" },
          title: "Excluded record",
          year: 2020,
          authors: ["Other Author"],
          source_title: "Other Journal",
        },
      ],
      warnings: [],
      metadata: {
        status_counts: { candidate: 2 },
        total_results: 17,
        returned_count: 2,
        requested_limit: 12,
        client_package: "pymedx",
        ncbi_database: "pmc",
      },
    };
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        const datasets = activeDatasetId
          ? [
              {
                dataset_id: activeDatasetId,
                created_at: "2026-01-01T00:00:00Z",
                records: 2,
                upload_ids: [],
              },
            ]
          : [];
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Remote project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: activeDatasetId,
              source_files: [],
              datasets,
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/datasets/dataset-1/summary")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              documents: 2,
              sources: 2,
              authors: 1,
              keywords: 0,
              timespan_start: null,
              timespan_end: null,
              documents_with_doi: 1,
              warnings: [],
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/datasets/dataset-1/analysis/overview")
      ) {
        return Promise.resolve(
          jsonResponse({
            data: {
              main_information: { documents: 2, sources: 2 },
              annual_production: [],
              top_authors: [],
              top_sources: [],
              top_keywords: [],
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads")) {
        return Promise.resolve(
          jsonResponse({ data: [], warnings: [], metadata: {} }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs") &&
        method === "GET"
      ) {
        return Promise.resolve(
          jsonResponse({ data: [], warnings: [], metadata: {} }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs/search-1") &&
        method === "GET"
      ) {
        return Promise.resolve(
          jsonResponse({ data: stagedSearch, warnings: [], metadata: {} }),
        );
      }
      if (url.endsWith("/projects/project-1/screening/runs")) {
        searchBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({ data: stagedSearch, warnings: [], metadata: {} }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs/search-1/candidates")
      ) {
        decisionBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            data: {
              ...stagedSearch,
              status_counts: { selected: 2 },
              candidates: stagedSearch.candidates.map((candidate) => ({
                ...candidate,
                status: "selected",
              })),
              metadata: { status_counts: { selected: 2 } },
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/screening/runs/search-1/promote")) {
        promoteBodies.push(JSON.parse(String(init?.body)));
        activeDatasetId = "dataset-1";
        return Promise.resolve(
          jsonResponse({
            data: {
              dataset_id: "dataset-1",
              created_at: "2026-01-01T00:00:00Z",
              upload_ids: [],
              records: [{ title: "PMC record" }, { title: "Excluded record" }],
              warnings: [],
              metadata: {
                source: "pmc",
                query: "open science",
                screening_run_id: "search-1",
              },
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    await screen.findByRole("heading", { name: /Search remote sources/i });
    await userEvent.selectOptions(screen.getByLabelText("Source"), "pmc");
    await userEvent.clear(screen.getByLabelText("Limit"));
    await userEvent.type(screen.getByLabelText("Limit"), "12");
    await userEvent.type(
      screen.getByLabelText("Contact email"),
      "r@example.org",
    );
    await userEvent.type(screen.getByLabelText("NCBI API key"), "secret-token");
    await userEvent.clear(screen.getByLabelText("Tool name"));
    await userEvent.type(
      screen.getByLabelText("Screening run name"),
      "PMC import",
    );
    await userEvent.type(screen.getByLabelText("Query"), "open science");
    await userEvent.click(
      screen.getByRole("button", { name: /Search and review records/i }),
    );

    await waitFor(() => expect(searchBodies).toHaveLength(1));
    expect(searchBodies[0]).toEqual({
      origin_type: "remote_search",
      source: "pmc",
      query: "open science",
      limit: 12,
      email: "r@example.org",
      api_key: "secret-token",
      tool: "biblioflow-web",
      name: "PMC import",
    });
    expect(await screen.findByText("PMC record")).toBeDefined();
    expect(screen.getByText(/Selected 2 records/i)).toBeDefined();
    expect(screen.getByText("Total matches")).toBeDefined();
    expect(screen.getByText("17")).toBeDefined();
    expect(screen.getByText("pymedx")).toBeDefined();

    await userEvent.type(screen.getByLabelText("Filter candidates"), "Grace");
    expect(screen.getByText(/Selected 2 records \(1 visible\)/i)).toBeDefined();
    await userEvent.click(
      screen.getByRole("button", { name: /Clear visible/i }),
    );
    expect(screen.getByText(/Selected 1 records \(0 visible\)/i)).toBeDefined();
    await userEvent.click(screen.getByRole("button", { name: /Uncheck all/i }));
    expect(screen.getByText(/Selected 0 records \(0 visible\)/i)).toBeDefined();
    await userEvent.click(screen.getByRole("button", { name: /^Check all$/i }));
    expect(screen.getByText(/Selected 2 records \(1 visible\)/i)).toBeDefined();
    await userEvent.click(
      screen.getByRole("button", { name: /Clear visible/i }),
    );
    expect(screen.getByText(/Selected 1 records \(0 visible\)/i)).toBeDefined();
    await userEvent.click(
      screen.getByRole("button", { name: /Select visible/i }),
    );
    expect(screen.getByText(/Selected 2 records \(1 visible\)/i)).toBeDefined();

    await userEvent.click(
      screen.getByRole("button", { name: /Mark selected as keep/i }),
    );
    await waitFor(() => expect(decisionBodies).toHaveLength(1));
    expect(decisionBodies[0]).toEqual({
      candidate_ids: ["candidate-2", "candidate-1"],
      status: "selected",
    });

    await userEvent.click(
      screen.getByRole("button", { name: /Create dataset from selected/i }),
    );
    await waitFor(() => expect(promoteBodies).toHaveLength(1));
    expect(promoteBodies[0]).toEqual({
      candidate_ids: ["candidate-2", "candidate-1"],
      name: "PMC import",
    });
    expect(await screen.findByText(/Created dataset/i)).toBeDefined();
    expect(screen.getByText("dataset-1")).toBeDefined();
    expect(
      screen.getAllByRole("link", { name: /Go to dashboard/i }).length,
    ).toBeGreaterThan(0);
    await userEvent.click(
      screen.getAllByRole("link", { name: /Go to dashboard/i }).at(-1)!,
    );
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringMatching(
          /\/projects\/project-1\/datasets\/dataset-1\/summary$/,
        ),
        expect.anything(),
      ),
    );
  });

  it("displays backend remote import errors", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Remote project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads")) {
        return Promise.resolve(
          jsonResponse({ data: [], warnings: [], metadata: {} }),
        );
      }
      if (url.endsWith("/projects/project-1/screening/runs")) {
        return Promise.resolve(
          jsonResponse(
            {
              error: {
                message:
                  "Pass an email or set BIBLIOFLOW_NCBI_EMAIL on the backend.",
              },
            },
            { status: 400 },
          ),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    await screen.findByRole("heading", { name: /Search remote sources/i });
    await userEvent.type(screen.getByLabelText("Query"), "bibliometrics");
    await userEvent.click(
      screen.getByRole("button", { name: /Search and review records/i }),
    );

    expect((await screen.findByRole("alert")).textContent).toMatch(
      /BIBLIOFLOW_NCBI_EMAIL/i,
    );
  });

  it("reviews staged search history and surfaces screening action errors", async () => {
    const decisionBodies: unknown[] = [];
    const promoteBodies: unknown[] = [];
    const historySearch = {
      screening_run_id: "search-1",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      source: "pubmed",
      source_label: "PubMed",
      query: "history",
      limit: 2,
      name: "History run",
      records: 2,
      status_counts: { candidate: 2 },
      candidates: [
        {
          candidate_id: "candidate-empty",
          status: "candidate",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          record: { title: "Sparse record" },
          identifiers: {},
          title: "Sparse record",
          year: null,
          authors: [],
          source_title: null,
        },
        {
          candidate_id: "candidate-promote-error",
          status: "candidate",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          record: { title: "Promote error record", pmid: "77" },
          identifiers: { pmid: "77" },
          title: "Promote error record",
          year: 2026,
          authors: ["Error Author"],
          source_title: "Error Journal",
        },
      ],
      warnings: [],
      metadata: { status_counts: { candidate: 2 } },
    };
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "History project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads")) {
        return Promise.resolve(
          jsonResponse({ data: [], warnings: [], metadata: {} }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs") &&
        method === "GET"
      ) {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                screening_run_id: "other-search",
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:00Z",
                source: "pubmed",
                source_label: "PubMed",
                query: "other",
                limit: 1,
                name: "Other run",
                records: 1,
                status_counts: { imported: 1 },
                metadata: {},
              },
              {
                screening_run_id: "search-1",
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:00Z",
                source: "pubmed",
                source_label: "PubMed",
                query: "history",
                limit: 2,
                name: "History run",
                records: 2,
                status_counts: { candidate: 2 },
                metadata: {},
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs/search-1") &&
        method === "GET"
      ) {
        return Promise.resolve(
          jsonResponse({ data: historySearch, warnings: [], metadata: {} }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs/search-1/candidates")
      ) {
        decisionBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            data: {
              ...historySearch,
              status_counts: { excluded: 1, candidate: 1 },
              candidates: [
                { ...historySearch.candidates[0], status: "excluded" },
                historySearch.candidates[1],
              ],
              metadata: { status_counts: { excluded: 1, candidate: 1 } },
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/screening/runs/search-1/promote")) {
        promoteBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse(
            { error: { message: "Promotion failed" } },
            { status: 500 },
          ),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectScreening();

    await userEvent.click(
      await screen.findByRole("button", { name: /History run · 2/i }),
    );
    expect(await screen.findByText("Sparse record")).toBeDefined();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);

    await userEvent.click(screen.getByLabelText("Select Sparse record"));
    expect(screen.getByText(/Selected 1 records/i)).toBeDefined();
    await userEvent.click(
      screen.getByRole("button", { name: /Exclude selected/i }),
    );
    await waitFor(() => expect(decisionBodies).toHaveLength(1));
    expect(decisionBodies[0]).toEqual({
      candidate_ids: ["candidate-empty"],
      status: "excluded",
    });
    expect(await screen.findByText(/Selected 0 records/i)).toBeDefined();

    await userEvent.click(screen.getByLabelText("Select Promote error record"));
    await userEvent.click(
      screen.getByRole("button", { name: /Create dataset from selected/i }),
    );
    await waitFor(() => expect(promoteBodies).toHaveLength(1));
    expect(promoteBodies[0]).toEqual({
      candidate_ids: ["candidate-promote-error"],
      name: "History run",
    });
    expect((await screen.findByRole("alert")).textContent).toMatch(
      /Promotion failed/i,
    );
  });

  it("shows all staged records together with duplicate groups", async () => {
    const bulkDecisionBodies: unknown[] = [];
    const firstCandidate = {
      candidate_id: "candidate-1",
      status: "candidate",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      record: { title: "Shared duplicate", doi: "10.1/shared" },
      identifiers: { doi: "10.1/shared" },
      deduplication_key: "doi:10.1/shared",
      duplicate_group_id: "doi:10.1/shared",
      duplicate_group_size: 2,
      duplicate_match_basis: "DOI",
      duplicate_confidence: "high",
      title: "Shared duplicate",
      year: 2026,
      authors: ["Ada Lovelace"],
      source_title: "Methods Journal",
      screening_run_id: "first-run",
      screening_run_name: "First import",
      source: "generic",
      source_label: "Generic",
      origin_type: "records",
      id: "first-run:candidate-1",
    };
    const secondCandidate = {
      ...firstCandidate,
      candidate_id: "candidate-2",
      screening_run_id: "second-run",
      screening_run_name: "Second import",
      id: "second-run:candidate-2",
      title: "Shared duplicate from another source",
      record: {
        title: "Shared duplicate from another source",
        doi: "10.1/shared",
      },
    };
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "All staged project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/screening/runs")) {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                screening_run_id: "first-run",
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:00Z",
                source: "generic",
                source_label: "Generic",
                origin_type: "records",
                name: "First import",
                records: 1,
                status_counts: { candidate: 1 },
                metadata: {},
              },
              {
                screening_run_id: "second-run",
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:00Z",
                source: "generic",
                source_label: "Generic",
                origin_type: "records",
                name: "Second import",
                records: 1,
                status_counts: { candidate: 1 },
                metadata: {},
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/candidates") &&
        method === "PATCH"
      ) {
        bulkDecisionBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            data: {
              records: 2,
              runs: [],
              candidates: [
                { ...firstCandidate, status: "excluded" },
                { ...secondCandidate, status: "excluded" },
              ],
              status_counts: { excluded: 2 },
              duplicate_groups: [
                {
                  duplicate_group_id: "doi:10.1/shared",
                  match_basis: "DOI",
                  confidence: "high",
                  size: 2,
                  candidate_ids: ["candidate-1", "candidate-2"],
                  screening_run_ids: ["first-run", "second-run"],
                  screening_run_names: ["First import", "Second import"],
                  label: "Shared duplicate",
                  years: [2026],
                  source_labels: ["Generic"],
                },
              ],
              metadata: {
                run_count: 2,
                duplicate_group_count: 1,
                duplicate_candidate_count: 2,
              },
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/candidates") &&
        method === "GET"
      ) {
        return Promise.resolve(
          jsonResponse({
            data: {
              records: 2,
              runs: [],
              candidates: [firstCandidate, secondCandidate],
              status_counts: { candidate: 2 },
              duplicate_groups: [
                {
                  duplicate_group_id: "doi:10.1/shared",
                  match_basis: "DOI",
                  confidence: "high",
                  size: 2,
                  candidate_ids: ["candidate-1", "candidate-2"],
                  screening_run_ids: ["first-run", "second-run"],
                  screening_run_names: ["First import", "Second import"],
                  label: "Shared duplicate",
                  years: [2026],
                  source_labels: ["Generic"],
                },
              ],
              metadata: {
                run_count: 2,
                duplicate_group_count: 1,
                duplicate_candidate_count: 2,
              },
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectScreening("first-run", "view=all");

    expect(
      await screen.findByRole("region", { name: /All staged records/i }),
    ).toBeDefined();
    expect(screen.getByText(/Project-level staging queue/i)).toBeDefined();
    expect(screen.getAllByText(/Shared duplicate/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/DOI · 2 records/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("First import").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Second import").length).toBeGreaterThan(0);

    await userEvent.click(
      screen.getByRole("button", { name: /Select visible/i }),
    );
    expect(screen.getByText(/Selected 2 records/i)).toBeDefined();
    await userEvent.click(screen.getByRole("button", { name: /Uncheck all/i }));
    expect(screen.getByText(/Selected 0 records/i)).toBeDefined();
    await userEvent.click(screen.getByRole("button", { name: /^Check all$/i }));
    expect(screen.getByText(/Selected 2 records/i)).toBeDefined();
    await userEvent.click(
      screen.getByRole("button", { name: /Exclude selected/i }),
    );
    await waitFor(() => expect(bulkDecisionBodies).toHaveLength(1));
    expect(bulkDecisionBodies[0]).toEqual({
      candidates: [
        { screening_run_id: "first-run", candidate_id: "candidate-1" },
        { screening_run_id: "second-run", candidate_id: "candidate-2" },
      ],
      status: "excluded",
    });
    expect(await screen.findByText(/excluded: 2/i)).toBeDefined();
  });

  it("deletes a staged import after confirmation", async () => {
    const deletedRunIds: string[] = [];
    let deleted = false;
    const confirmMock = vi.fn(() => true);
    vi.stubGlobal("confirm", confirmMock);
    const run = {
      screening_run_id: "run-1",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      source: "pubmed",
      source_label: "PubMed",
      origin_type: "remote_search",
      format: "api",
      query: "wrong query",
      upload_ids: [],
      limit: 10,
      name: "Wrong PubMed import",
      records: 1,
      status_counts: { candidate: 1 },
      promoted_dataset_ids: ["dataset-1"],
      candidates: [
        {
          candidate_id: "candidate-1",
          status: "candidate",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          record: { title: "Wrong record", pmid: "123" },
          identifiers: { pmid: "123" },
          title: "Wrong record",
          year: 2024,
          authors: ["Jane Smith"],
          source_title: "Wrong Journal",
        },
      ],
      warnings: [],
      metadata: {},
    };
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Delete staged project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: "dataset-1",
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs/run-1") &&
        method === "DELETE"
      ) {
        deleted = true;
        deletedRunIds.push("run-1");
        return Promise.resolve(
          jsonResponse({
            data: {
              deleted: true,
              screening_run_id: "run-1",
              name: "Wrong PubMed import",
              records: 1,
              promoted_dataset_ids: ["dataset-1"],
              datasets_preserved: true,
            },
            warnings: [{ message: "Datasets were preserved." }],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs/run-1") &&
        method === "GET"
      ) {
        return Promise.resolve(
          deleted
            ? jsonResponse(
                { error: { message: "Screening run was not found." } },
                { status: 404 },
              )
            : jsonResponse({ data: run, warnings: [], metadata: {} }),
        );
      }
      if (url.endsWith("/projects/project-1/screening/runs")) {
        return Promise.resolve(
          jsonResponse({
            data: deleted ? [] : [{ ...run, candidates: undefined }],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/screening/candidates")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              records: deleted ? 0 : 1,
              runs: deleted ? [] : [{ ...run, candidates: undefined }],
              candidates: deleted ? [] : [],
              status_counts: deleted ? {} : { candidate: 1 },
              duplicate_groups: [],
              metadata: {
                run_count: deleted ? 0 : 1,
                duplicate_group_count: 0,
                duplicate_candidate_count: 0,
              },
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectScreening("run-1");

    expect(await screen.findByText("Wrong PubMed import")).toBeDefined();
    await userEvent.click(
      screen.getByRole("button", { name: /Delete staged import/i }),
    );

    await waitFor(() => expect(deletedRunIds).toEqual(["run-1"]));
    expect(confirmMock).toHaveBeenCalledWith(
      expect.stringContaining("Wrong PubMed import"),
    );
    expect(confirmMock).toHaveBeenCalledWith(
      expect.stringContaining("dataset was already created"),
    );
  });

  it("renders upload size formats and ignores empty file events", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Size project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads")) {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-kb",
                filename: "medium.ris",
                content_type: "application/x-research-info-systems",
                size: 2048,
                created_at: "2026-01-01T00:00:00Z",
              },
              {
                upload_id: "upload-mb",
                filename: "large.bib",
                content_type: "application/x-bibtex",
                size: 2 * 1024 * 1024,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const { container } = renderProjectUpload();

    expect(await screen.findByText("2.0 KB")).toBeDefined();
    expect(await screen.findByText("2.0 MB")).toBeDefined();

    const dropzone = screen
      .getByText("Upload bibliographic files")
      .closest("label");
    expect(dropzone).not.toBeNull();
    fireEvent.dragOver(dropzone as HTMLLabelElement);
    fireEvent.drop(dropzone as HTMLLabelElement, {
      dataTransfer: { files: [] },
    });

    const input =
      container.querySelector<HTMLInputElement>("input[type='file']");
    expect(input).not.toBeNull();
    fireEvent.change(input as HTMLInputElement, {
      target: { files: null },
    });
    expect(screen.queryByText("Ready to upload")).toBeNull();
  });

  it("displays upload list errors", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Upload errors",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads")) {
        return Promise.resolve(
          jsonResponse(
            { error: { message: "Unable to load uploads." } },
            { status: 500 },
          ),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    expect((await screen.findByRole("alert")).textContent).toMatch(
      /Unable to load uploads\./i,
    );
  });

  it("displays upload mutation, delete, and dataset load errors", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Mutation errors",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "GET") {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-1",
                filename: "minimal.json",
                content_type: "application/json",
                size: 42,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "POST") {
        return Promise.resolve(
          jsonResponse(
            { error: { message: "Upload failed" } },
            { status: 400 },
          ),
        );
      }
      if (
        url.endsWith("/projects/project-1/uploads/upload-1") &&
        method === "DELETE"
      ) {
        return Promise.resolve(
          jsonResponse(
            { error: { message: "Delete failed" } },
            { status: 500 },
          ),
        );
      }
      if (url.endsWith("/projects/project-1/datasets/load")) {
        return Promise.resolve(
          jsonResponse({ error: { message: "Load failed" } }, { status: 422 }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const { container } = renderProjectUpload();

    await screen.findByText("minimal.json");
    await userEvent.click(screen.getByRole("button", { name: /Delete/i }));
    expect(await screen.findByText("Delete failed")).toBeDefined();

    const input =
      container.querySelector<HTMLInputElement>("input[type='file']");
    expect(input).not.toBeNull();
    await userEvent.upload(
      input as HTMLInputElement,
      new File(["{}"], "records.json", { type: "application/json" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: /Upload selected files/i }),
    );
    expect(await screen.findByText("Upload failed")).toBeDefined();

    await userEvent.click(
      screen.getByRole("button", { name: /Load directly/i }),
    );
    expect(await screen.findByText("Load failed")).toBeDefined();
  });

  it("uploads files and loads selected uploads", async () => {
    const uploadedFiles: string[] = [];
    const loadBodies: unknown[] = [];
    const screeningBodies: unknown[] = [];
    const decisionBodies: unknown[] = [];
    const deletedUploadIds: string[] = [];
    const uploadScreeningRun = {
      screening_run_id: "upload-run-1",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      origin_type: "uploads",
      source: "wos",
      source_label: "Web of Science",
      format: "ris",
      query: null,
      upload_ids: ["upload-2"],
      limit: 100,
      name: "Uploaded files: 1 selected",
      records: 2,
      status_counts: { candidate: 1, duplicate: 1 },
      promoted_dataset_ids: [],
      candidates: [
        {
          candidate_id: "upload-candidate-1",
          status: "candidate",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          record: { title: "Uploaded candidate", doi: "10.1/upload" },
          identifiers: { doi: "10.1/upload" },
          title: "Uploaded candidate",
          year: 2024,
          authors: ["Upload Author"],
          source_title: "Upload Journal",
        },
        {
          candidate_id: "upload-candidate-duplicate",
          status: "duplicate",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          record: { title: "Duplicate upload", doi: "10.1/upload" },
          identifiers: { doi: "10.1/upload" },
          title: "Duplicate upload",
          year: 2024,
          authors: ["Upload Author"],
          source_title: "Upload Journal",
        },
      ],
      warnings: [],
      metadata: { status_counts: { candidate: 1, duplicate: 1 } },
    };
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Upload project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "GET") {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-1",
                filename: "minimal.json",
                content_type: "application/json",
                size: 42,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "POST") {
        const form = init?.body as FormData;
        uploadedFiles.push((form.get("files") as File).name);
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-2",
                filename: "records.json",
                content_type: "application/json",
                size: 2,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/uploads/upload-1") &&
        method === "DELETE"
      ) {
        deletedUploadIds.push("upload-1");
        return Promise.resolve(
          jsonResponse({
            data: { deleted: true },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs") &&
        method === "GET"
      ) {
        return Promise.resolve(
          jsonResponse({ data: [], warnings: [], metadata: {} }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs") &&
        method === "POST"
      ) {
        screeningBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            data: uploadScreeningRun,
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/screening/runs/upload-run-1") &&
        method === "GET"
      ) {
        return Promise.resolve(
          jsonResponse({
            data: uploadScreeningRun,
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith(
          "/projects/project-1/screening/runs/upload-run-1/candidates",
        )
      ) {
        const body = JSON.parse(String(init?.body));
        decisionBodies.push(body);
        return Promise.resolve(
          jsonResponse({
            data: {
              ...uploadScreeningRun,
              status_counts: { [body.status]: 1, duplicate: 1 },
              candidates: uploadScreeningRun.candidates.map((candidate) =>
                candidate.candidate_id === "upload-candidate-1"
                  ? { ...candidate, status: body.status }
                  : candidate,
              ),
              metadata: { status_counts: { [body.status]: 1, duplicate: 1 } },
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/datasets/load")) {
        loadBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            data: {
              dataset_id: "dataset-2",
              created_at: "2026-01-01T00:00:00Z",
              upload_ids: ["upload-1", "upload-2"],
              records: [{ title: "Loaded record" }],
              warnings: [],
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const { container } = renderProjectUpload();

    await screen.findByText("minimal.json");
    const checkbox = screen.getByLabelText("Select minimal.json");
    await userEvent.click(checkbox);
    await userEvent.click(checkbox);
    await userEvent.click(screen.getByRole("button", { name: /Delete/i }));
    await waitFor(() => expect(deletedUploadIds).toEqual(["upload-1"]));

    await userEvent.selectOptions(screen.getByLabelText("Provider"), "wos");
    await userEvent.selectOptions(screen.getByLabelText("Format"), "ris");

    const input =
      container.querySelector<HTMLInputElement>("input[type='file']");
    expect(input).not.toBeNull();
    const dropzone = screen
      .getByText("Upload bibliographic files")
      .closest("label");
    expect(dropzone).not.toBeNull();
    fireEvent.drop(dropzone as HTMLLabelElement, {
      dataTransfer: {
        files: [new File(["{}"], "dropped.json", { type: "application/json" })],
      },
    });
    expect(await screen.findByText(/dropped\.json · 2 B/i)).toBeDefined();
    await userEvent.click(screen.getByRole("button", { name: /Clear/i }));
    expect(screen.queryByText(/dropped\.json · 2 B/i)).toBeNull();

    await userEvent.upload(
      input as HTMLInputElement,
      new File(["{}"], "records.json", { type: "application/json" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: /Upload selected files/i }),
    );
    await waitFor(() => expect(uploadedFiles).toEqual(["records.json"]));

    await userEvent.click(
      screen.getByRole("button", { name: /Review selected uploads/i }),
    );
    await waitFor(() =>
      expect(screeningBodies).toEqual([
        {
          origin_type: "uploads",
          upload_ids: ["upload-2"],
          source: "wos",
          format: "ris",
          name: "Uploaded files: 1 selected",
        },
      ]),
    );
    expect(await screen.findByText("Uploaded candidate")).toBeDefined();
    expect(screen.getByText("Duplicate upload")).toBeDefined();
    expect(await screen.findByText(/Selected 1 records/i)).toBeDefined();
    await userEvent.click(
      screen.getByRole("button", { name: /Mark as maybe/i }),
    );
    await waitFor(() =>
      expect(decisionBodies).toContainEqual({
        candidate_ids: ["upload-candidate-1"],
        status: "maybe",
      }),
    );
    await userEvent.click(screen.getByLabelText("Select Uploaded candidate"));
    expect(screen.getByText(/Selected 0 records/i)).toBeDefined();
    await userEvent.click(
      screen.getByRole("button", { name: /Select visible/i }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: /Mark duplicate/i }),
    );
    await waitFor(() =>
      expect(decisionBodies).toContainEqual({
        candidate_ids: ["upload-candidate-1"],
        status: "duplicate",
      }),
    );
  });

  it("routes to validation when loading a dataset returns warnings", async () => {
    const loadBodies: unknown[] = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Warning project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "GET") {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-1",
                filename: "warning.json",
                content_type: "application/json",
                size: 42,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/datasets/load")) {
        loadBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            data: {
              dataset_id: "dataset-warning",
              created_at: "2026-01-01T00:00:00Z",
              upload_ids: ["upload-1"],
              records: [{ title: "Warning record" }],
              warnings: [{ message: "Review imported metadata" }],
              metadata: {},
            },
            warnings: [{ message: "Review imported metadata" }],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    await screen.findByText("warning.json");
    await userEvent.click(
      screen.getByRole("button", { name: /Load directly/i }),
    );
    await waitFor(() =>
      expect(loadBodies).toEqual([
        { upload_ids: ["upload-1"], provider: "auto", format: "auto" },
      ]),
    );
  });
});
