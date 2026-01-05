'use client';

import { useState, useEffect } from 'react';
import adminConfigService from '@/services/admin-config.service';
import { Sparkles, X } from 'lucide-react';

interface Suggestion {
  rule_name: string;
  intent: string;
  target_domain: string;
  id: string;
}

interface RuleNameSuggestionsProps {
  targetIntent?: string;
  targetDomain?: string;
  onSelect?: (suggestion: Suggestion) => void;
}

export default function RuleNameSuggestions({
  targetIntent,
  targetDomain,
  onSelect,
}: RuleNameSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    loadSuggestions();
  }, [targetIntent, targetDomain]);

  const loadSuggestions = async () => {
    try {
      setLoading(true);
      const response = await adminConfigService.getRoutingRuleSuggestions();
      let filtered = response.suggestions || [];

      // Filter by target intent if provided
      if (targetIntent) {
        filtered = filtered.filter((s) => s.intent === targetIntent);
      }

      // Filter by target domain if provided
      if (targetDomain) {
        filtered = filtered.filter((s) => s.target_domain === targetDomain);
      }

      setSuggestions(filtered);
    } catch (error: any) {
      console.error('Failed to load suggestions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setShowSuggestions(!showSuggestions)}
        className="flex items-center text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
      >
        <Sparkles className="h-4 w-4 mr-1" />
        {showSuggestions ? 'Ẩn' : 'Hiển thị'} gợi ý rule name từ routing rules ({suggestions.length})
      </button>

      {showSuggestions && (
        <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
              Gợi ý từ Routing Rules:
            </p>
            <button
              type="button"
              onClick={() => setShowSuggestions(false)}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="space-y-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion.id}
                type="button"
                onClick={() => {
                  if (onSelect) {
                    onSelect(suggestion);
                  }
                }}
                className="w-full text-left p-2 bg-white dark:bg-gray-800 rounded border border-blue-200 dark:border-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {suggestion.rule_name}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Intent: <code className="text-primary-600 dark:text-primary-400">{suggestion.intent}</code> | Domain: <code className="text-primary-600 dark:text-primary-400">{suggestion.target_domain}</code>
                    </p>
                  </div>
                  <span className="text-xs text-blue-600 dark:text-blue-400">Click để dùng</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

