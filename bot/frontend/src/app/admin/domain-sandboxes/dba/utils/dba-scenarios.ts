export interface DBAScenario {
  id: string;
  title: string;
  description: string;
  expectedRisks: string[];
  intent: string;
  defaultQuery?: string;
}

export const DBA_SCENARIOS: Record<string, DBAScenario> = {
  slow_query_analysis: {
    id: 'slow_query_analysis',
    title: 'Analyze Slow Queries',
    description: 'Find slow running queries on database',
    expectedRisks: ['wrong_db_selected', 'permission_denied', 'query_too_slow'],
    intent: 'analyze_slow_query',
  },

  check_deadlocks: {
    id: 'check_deadlocks',
    title: 'Detect Deadlocks',
    description: 'Check for blocking and deadlock patterns',
    expectedRisks: ['connection_failure', 'permission_denied'],
    intent: 'detect_deadlock_pattern',
  },

  check_index_health: {
    id: 'check_index_health',
    title: 'Check Index Health',
    description: 'Check database index health and fragmentation',
    expectedRisks: ['permission_denied', 'performance_acceptable'],
    intent: 'check_index_health',
  },

  analyze_wait_stats: {
    id: 'analyze_wait_stats',
    title: 'Analyze Wait Statistics',
    description: 'Analyze database wait statistics',
    expectedRisks: ['query_too_slow', 'permission_denied'],
    intent: 'analyze_wait_stats',
  },

  validate_custom_sql: {
    id: 'validate_custom_sql',
    title: 'Validate Custom SQL',
    description: 'Check custom SQL before execution',
    expectedRisks: ['sql_injection', 'query_too_slow', 'permission_denied'],
    intent: 'validate_custom_sql',
    defaultQuery: 'SELECT * FROM sys.tables WHERE name LIKE \'%\'',
  },

  incident_triage: {
    id: 'incident_triage',
    title: 'Database Incident Triage',
    description: 'Analyze database incidents',
    expectedRisks: ['permission_denied', 'performance_acceptable'],
    intent: 'incident_triage',
  },
};

export const getScenario = (scenarioId: string): DBAScenario | undefined => {
  return DBA_SCENARIOS[scenarioId];
};

export const getScenariosList = (): DBAScenario[] => {
  return Object.values(DBA_SCENARIOS);
};
