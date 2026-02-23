'use client';

import { Component, ReactNode } from 'react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
                    <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 text-center">
                        <div className="text-6xl mb-4">😕</div>
                        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                            Đã xảy ra lỗi
                        </h1>
                        <p className="text-gray-600 dark:text-gray-400 mb-6">
                            Ứng dụng gặp sự cố không mong muốn. Vui lòng thử lại sau.
                        </p>
                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <details className="mb-4 text-left">
                                <summary className="cursor-pointer text-sm text-gray-500 dark:text-gray-400 mb-2">
                                    Chi tiết lỗi (Development)
                                </summary>
                                <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-3 rounded overflow-auto">
                                    {this.state.error.toString()}
                                    {this.state.error.stack}
                                </pre>
                            </details>
                        )}
                        <button
                            onClick={() => {
                                this.setState({ hasError: false, error: undefined });
                                window.location.reload();
                            }}
                            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Tải lại trang
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

