"""
Analytics Visualizations for Meton Web UI.

Generates interactive Plotly charts for:
- Performance metrics
- Tool usage
- Success rates
- Reflection scores
- Bottleneck analysis
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any, Optional


class MetonVisualizations:
    """Generate visualizations for web UI."""

    def __init__(self, analytics=None):
        """
        Initialize visualizations.

        Args:
            analytics: PerformanceAnalytics instance (optional for testing)
        """
        self.analytics = analytics

    def create_performance_chart(self) -> go.Figure:
        """
        Create response time trend chart.

        Returns:
            Plotly Figure
        """
        if not self.analytics:
            return self._create_empty_chart("No analytics data available")

        try:
            dashboard = self.analytics.get_dashboard()
            trend = dashboard.get("trends", {}).get("response_time_trend", [])

            if not trend:
                return self._create_empty_chart("No performance data yet")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                y=trend,
                mode='lines+markers',
                name='Response Time',
                line=dict(color='#3b82f6', width=2),
                marker=dict(size=6)
            ))

            # Add average line
            if trend:
                avg = sum(trend) / len(trend)
                fig.add_hline(
                    y=avg,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=f"Average: {avg:.2f}s"
                )

            fig.update_layout(
                title="Response Time Trend (Last 20 Queries)",
                xaxis_title="Query Number",
                yaxis_title="Time (seconds)",
                template="plotly_white",
                hovermode='x unified',
                showlegend=True
            )

            return fig

        except Exception as e:
            return self._create_empty_chart(f"Error: {str(e)}")

    def create_tool_usage_chart(self) -> go.Figure:
        """
        Create tool usage distribution chart.

        Returns:
            Plotly Figure
        """
        if not self.analytics:
            return self._create_empty_chart("No analytics data available")

        try:
            dashboard = self.analytics.get_dashboard()
            tools = dashboard.get("tools", {})

            if not tools:
                return self._create_empty_chart("No tool usage data yet")

            tool_names = list(tools.keys())
            usage_counts = [tools[t]["usage_count"] for t in tool_names]

            fig = go.Figure(data=[go.Bar(
                x=tool_names,
                y=usage_counts,
                marker_color='#8b5cf6',
                text=usage_counts,
                textposition='auto'
            )])

            fig.update_layout(
                title="Tool Usage Distribution",
                xaxis_title="Tool",
                yaxis_title="Usage Count",
                template="plotly_white",
                showlegend=False
            )

            return fig

        except Exception as e:
            return self._create_empty_chart(f"Error: {str(e)}")

    def create_success_rate_gauge(self) -> go.Figure:
        """
        Create success rate gauge chart.

        Returns:
            Plotly Figure
        """
        if not self.analytics:
            return self._create_empty_gauge(0, "No Data")

        try:
            dashboard = self.analytics.get_dashboard()
            success_rate = dashboard.get("overview", {}).get("success_rate", 0)

            # Convert to percentage
            success_pct = success_rate * 100

            # Determine color
            if success_pct >= 90:
                color = "green"
            elif success_pct >= 70:
                color = "orange"
            else:
                color = "red"

            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=success_pct,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Success Rate"},
                delta={'reference': 90},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 70], 'color': "lightgray"},
                        {'range': [70, 90], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))

            fig.update_layout(
                template="plotly_white",
                height=300
            )

            return fig

        except Exception as e:
            return self._create_empty_gauge(0, f"Error: {str(e)}")

    def create_reflection_scores_chart(self) -> go.Figure:
        """
        Create reflection quality scores chart.

        Returns:
            Plotly Figure
        """
        if not self.analytics:
            return self._create_empty_chart("No analytics data available")

        try:
            # Get reflection metrics from analytics
            # Note: This requires analytics to track reflection scores over time
            # For now, we'll create a placeholder

            dashboard = self.analytics.get_dashboard()
            reflection = dashboard.get("reflection", {})
            avg_score = reflection.get("avg_score", 0)
            count = reflection.get("count", 0)

            if count == 0:
                return self._create_empty_chart("No reflection data yet")

            # Create simple visualization
            fig = go.Figure()

            fig.add_trace(go.Indicator(
                mode="number+gauge",
                value=avg_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Average Reflection Quality ({count} queries)"},
                gauge={
                    'axis': {'range': [0, 1]},
                    'bar': {'color': "#10b981"},
                    'steps': [
                        {'range': [0, 0.5], 'color': "lightgray"},
                        {'range': [0.5, 0.7], 'color': "gray"}
                    ]
                }
            ))

            fig.update_layout(
                template="plotly_white",
                height=300
            )

            return fig

        except Exception as e:
            return self._create_empty_chart(f"Error: {str(e)}")

    def create_bottleneck_table(self) -> pd.DataFrame:
        """
        Create bottleneck analysis table.

        Returns:
            Pandas DataFrame
        """
        if not self.analytics:
            return pd.DataFrame({
                'Type': ['No Data'],
                'Severity': ['-'],
                'Message': ['Analytics not available']
            })

        try:
            bottlenecks = self.analytics.get_bottlenecks()

            if not bottlenecks:
                return pd.DataFrame({
                    'Type': ['No Issues'],
                    'Severity': ['✅'],
                    'Message': ['All systems operating normally']
                })

            # Convert to DataFrame
            data = []
            for bottleneck in bottlenecks:
                data.append({
                    'Type': bottleneck['type'].replace('_', ' ').title(),
                    'Severity': self._severity_to_emoji(bottleneck['severity']),
                    'Message': bottleneck['message']
                })

            return pd.DataFrame(data)

        except Exception as e:
            return pd.DataFrame({
                'Type': ['Error'],
                'Severity': ['❌'],
                'Message': [str(e)]
            })

    def create_metrics_summary(self) -> Dict[str, Any]:
        """
        Create summary metrics dictionary.

        Returns:
            Dictionary of metrics
        """
        if not self.analytics:
            return {
                "status": "No analytics available",
                "total_queries": 0,
                "success_rate": "0%",
                "avg_response_time": "0s",
                "total_tool_calls": 0
            }

        try:
            dashboard = self.analytics.get_dashboard()
            overview = dashboard.get("overview", {})

            return {
                "total_queries": overview.get("total_queries", 0),
                "success_rate": f"{overview.get('success_rate', 0) * 100:.1f}%",
                "avg_response_time": f"{overview.get('avg_response_time', 0):.2f}s",
                "total_tool_calls": overview.get("total_tool_calls", 0),
                "trend": dashboard.get("trends", {}).get("trend_direction", "stable")
            }

        except Exception as e:
            return {
                "status": f"Error: {str(e)}",
                "total_queries": 0,
                "success_rate": "0%",
                "avg_response_time": "0s",
                "total_tool_calls": 0
            }

    def create_query_types_chart(self) -> go.Figure:
        """
        Create query types distribution chart.

        Returns:
            Plotly Figure
        """
        if not self.analytics:
            return self._create_empty_chart("No analytics data available")

        try:
            dashboard = self.analytics.get_dashboard()
            query_types = dashboard.get("query_types", {})

            if not query_types:
                return self._create_empty_chart("No query type data yet")

            types = list(query_types.keys())
            counts = [query_types[t]["count"] for t in types]

            fig = go.Figure(data=[go.Pie(
                labels=types,
                values=counts,
                hole=0.3,
                marker_colors=['#3b82f6', '#8b5cf6', '#ec4899']
            )])

            fig.update_layout(
                title="Query Complexity Distribution",
                template="plotly_white",
                showlegend=True
            )

            return fig

        except Exception as e:
            return self._create_empty_chart(f"Error: {str(e)}")

    def create_tool_performance_table(self) -> pd.DataFrame:
        """
        Create detailed tool performance table.

        Returns:
            Pandas DataFrame
        """
        if not self.analytics:
            return pd.DataFrame({
                'Tool': ['No Data'],
                'Usage': [0],
                'Avg Time': ['0s'],
                'Success Rate': ['0%']
            })

        try:
            dashboard = self.analytics.get_dashboard()
            tools = dashboard.get("tools", {})

            if not tools:
                return pd.DataFrame({
                    'Tool': ['No Data'],
                    'Usage': [0],
                    'Avg Time': ['0s'],
                    'Success Rate': ['0%']
                })

            data = []
            for tool_name, stats in tools.items():
                data.append({
                    'Tool': tool_name,
                    'Usage': stats['usage_count'],
                    'Avg Time': f"{stats['avg_time']:.2f}s",
                    'Success Rate': f"{stats['success_rate'] * 100:.1f}%"
                })

            df = pd.DataFrame(data)
            # Sort by usage count
            df = df.sort_values('Usage', ascending=False)

            return df

        except Exception as e:
            return pd.DataFrame({
                'Tool': ['Error'],
                'Usage': [0],
                'Avg Time': ['0s'],
                'Success Rate': [str(e)]
            })

    def _create_empty_chart(self, message: str) -> go.Figure:
        """
        Create empty placeholder chart.

        Args:
            message: Message to display

        Returns:
            Plotly Figure
        """
        fig = go.Figure()

        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )

        fig.update_layout(
            template="plotly_white",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )

        return fig

    def _create_empty_gauge(self, value: float, message: str) -> go.Figure:
        """
        Create empty gauge chart.

        Args:
            value: Gauge value
            message: Message to display

        Returns:
            Plotly Figure
        """
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': message},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "lightgray"}
            }
        ))

        fig.update_layout(
            template="plotly_white",
            height=300
        )

        return fig

    def _severity_to_emoji(self, severity: str) -> str:
        """
        Convert severity level to emoji.

        Args:
            severity: Severity level

        Returns:
            Emoji string
        """
        severity_map = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }

        return severity_map.get(severity.lower(), '⚪')
