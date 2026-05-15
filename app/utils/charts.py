"""توابع نمودار — Plotly تعاملی"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json


RTL_LAYOUT = dict(
    font=dict(family="Vazirmatn, sans-serif", size=13),
    plot_bgcolor='#FFFFFF',
    paper_bgcolor='#FFFFFF',
    margin=dict(l=60, r=40, t=60, b=60),
)


def yearly_bar(data: list[dict], title: str = 'توزیع سالانه') -> go.Figure:
    df = pd.DataFrame(data)
    if df.empty:
        return go.Figure()
    # فقط سال‌های شمسی معتبر ۱۳۵۶–۱۴۰۴
    df = df[df['year'].str.match(r'^1[3-4]\d{2}$', na=False)]
    fig = px.bar(df, x='year', y='cnt',
                 labels={'year': 'سال شمسی', 'cnt': 'تعداد سند'},
                 title=title, color_discrete_sequence=['#E91E63'])
    fig.update_layout(**RTL_LAYOUT)
    fig.update_layout(xaxis=dict(tickangle=-45, range=['1356', '1405']))
    return fig


PERIOD_FA = {
    'pre_revolution':   'قبل از انقلاب (۵۶–۵۷)',
    'early_revolution': 'اوایل انقلاب (۵۸–۵۹)',
    'presidency':       'ریاست‌جمهوری خامنه‌ای (۶۰–۶۷)',
    'hashemi':          'دوره هاشمی (۶۸–۷۵)',
    'khatami':          'دوره خاتمی (۷۶–۸۳)',
    'ahmadinejad':      'دوره احمدی‌نژاد (۸۴–۹۱)',
    'rouhani':          'دوره روحانی (۹۲–۹۹)',
    'raisi_to_death':   'دوره رئیسی (۱۴۰۰–)',
}


def period_bar(data: list[dict]) -> go.Figure:
    df = pd.DataFrame(data)
    if df.empty:
        return go.Figure()
    df['label_fa'] = df['period_label'].map(lambda x: PERIOD_FA.get(x, x))
    fig = px.bar(df, x='cnt', y='label_fa', orientation='h',
                 labels={'cnt': 'تعداد سند', 'label_fa': 'دوره'},
                 color='cnt', color_continuous_scale='Blues')
    fig.update_layout(**RTL_LAYOUT)
    fig.update_layout(
        yaxis=dict(autorange='reversed', tickfont=dict(size=12)),
        margin=dict(l=230, r=40, t=20, b=40),
        coloraxis_showscale=False,
    )
    return fig


def tier_pie(data: list[dict]) -> go.Figure:
    df = pd.DataFrame(data)
    if df.empty:
        return go.Figure()
    fig = px.pie(df, values='cnt', names='tier',
                 title='توزیع بر tier',
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(**RTL_LAYOUT)
    return fig


def genre_treemap(data: list[dict]) -> go.Figure:
    df = pd.DataFrame(data)
    if df.empty:
        return go.Figure()
    df = df.sort_values('cnt', ascending=True).tail(25)
    fig = px.bar(df, x='cnt', y='genre', orientation='h',
                 labels={'cnt': 'تعداد سند', 'genre': 'ژانر'},
                 title='توزیع بر ژانر (form_genre)',
                 color='cnt', color_continuous_scale='Reds',
                 text='cnt')
    fig.update_traces(textposition='outside')
    layout = dict(**RTL_LAYOUT)
    layout['margin'] = dict(l=220, r=60, t=60, b=40)
    fig.update_layout(**layout)
    fig.update_yaxes(automargin=True)
    return fig


def tone_bar(data: list[dict]) -> go.Figure:
    df = pd.DataFrame(data)
    if df.empty:
        return go.Figure()
    df = df.sort_values('cnt', ascending=True).tail(20)
    fig = px.bar(df, x='cnt', y='tone', orientation='h',
                 labels={'cnt': 'تعداد', 'tone': 'لحن'},
                 title='توزیع بر لحن (tag_tone)',
                 color='cnt', color_continuous_scale='Reds')
    fig.update_layout(**RTL_LAYOUT)
    return fig


def keyword_trend(trend_data: dict) -> go.Figure:
    """خط چندسری برای تطور کلیدواژه"""
    fig = go.Figure()
    colors = ['#E91E63', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
    for i, (kw, year_counts) in enumerate(trend_data.items()):
        years = sorted(year_counts.keys())
        counts = [year_counts[y] for y in years]
        fig.add_trace(go.Scatter(
            x=years, y=counts, mode='lines+markers',
            name=kw, line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=5),
        ))
    fig.update_layout(**RTL_LAYOUT,
        title='تطور کلیدواژه در طول زمان',
        xaxis_title='سال شمسی',
        yaxis_title='تعداد سند',
        legend=dict(x=0, y=1),
        hovermode='x unified',
    )
    return fig


def topic_period_heatmap(data: list[dict]) -> go.Figure:
    if not data:
        return go.Figure()
    df = pd.DataFrame(data)
    pivot = df.pivot_table(index='topic', columns='period', values='cnt', fill_value=0)
    fig = px.imshow(pivot,
                    title='heatmap دوره × موضوع',
                    color_continuous_scale='Reds',
                    aspect='auto')
    layout = dict(**RTL_LAYOUT)
    layout['margin'] = dict(l=250, r=40, t=80, b=60)
    fig.update_layout(**layout)
    fig.update_yaxes(automargin=True, tickfont=dict(size=11))
    fig.update_xaxes(automargin=True)
    return fig


def topic_cooccurrence(data: pd.DataFrame) -> go.Figure:
    if data is None or data.empty:
        return go.Figure()
    short_labels = {l: l[:14] for l in data.index}
    data_short = data.rename(index=short_labels, columns=short_labels)
    fig = go.Figure(go.Heatmap(
        z=data_short.values,
        x=list(data_short.columns),
        y=list(data_short.index),
        colorscale='Reds',
        text=data_short.values,
        texttemplate='%{text}',
        hovertemplate='%{y} × %{x}<br>همرخدادی: %{z}<extra></extra>',
        showscale=True,
    ))
    fig.update_layout(
        title='همرخدادی موضوعات — هر سلول تعداد سندی که هر دو موضوع دارد',
        font=dict(family="Vazirmatn, sans-serif", size=11),
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
        margin=dict(l=250, r=40, t=80, b=250),
        height=700,
    )
    fig.update_xaxes(automargin=True, tickangle=-45)
    fig.update_yaxes(automargin=True)
    return fig


def region_bar(data: list[dict]) -> go.Figure:
    df = pd.DataFrame(data)
    if df.empty:
        return go.Figure()
    df = df.sort_values('cnt', ascending=True).tail(25)
    fig = px.bar(df, x='cnt', y='region', orientation='h',
                 labels={'cnt': 'تعداد', 'region': 'منطقه'},
                 title='توزیع منطقه‌ای (tag_regions)',
                 color='cnt', color_continuous_scale='Blues')
    fig.update_layout(**RTL_LAYOUT)
    return fig


def fig_to_json(fig: go.Figure) -> str:
    return fig.to_json()
