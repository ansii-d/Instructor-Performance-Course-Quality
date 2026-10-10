
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def experience_scatter(teachers):
    """Plot instructor experience against teacher ratings."""
    required = ["YearsOfExperience", "TeacherRating", "Expertise"]
    missing = [col for col in required if col not in teachers.columns]

    if missing:
        raise ValueError(
            f"Missing columns for experience chart: {missing}"
        )

    plot_data = teachers[required].copy()

    plot_data["YearsOfExperience"] = pd.to_numeric(
        plot_data["YearsOfExperience"], errors="coerce"
    )
    plot_data["TeacherRating"] = pd.to_numeric(
        plot_data["TeacherRating"], errors="coerce"
    )

    plot_data = plot_data.dropna(
        subset=["YearsOfExperience", "TeacherRating"]
    )

    if plot_data.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Instructor Experience vs Teacher Rating",
            xaxis_title="Years of Experience",
            yaxis_title="Teacher Rating (out of 5)",
            template="plotly_dark",
            height=480,
            annotations=[
                {
                    "text": "No valid instructor data available",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                }
            ],
        )
        return fig

    fig = px.scatter(
        plot_data,
        x="YearsOfExperience",
        y="TeacherRating",
        color="Expertise",
        hover_data=["Expertise"],
        title="Instructor Experience vs Teacher Rating",
        labels={
            "YearsOfExperience": "Years of Experience",
            "TeacherRating": "Teacher Rating (out of 5)",
            "Expertise": "Instructor Expertise",
        },
    )

    fig.update_traces(
        mode="markers",
        marker={"size": 10, "opacity": 0.8},
    )
    fig.update_layout(
        template="plotly_dark",
        height=480,
        xaxis_title="Years of Experience",
        yaxis_title="Teacher Rating (out of 5)",
        yaxis={"range": [0, 5]},
        legend_title_text="Instructor Expertise",
    )

    return fig


def expertise_bar(expertise_data):
    """Compare average teacher ratings by expertise."""
    required = ["AverageTeacherRating", "Expertise"]
    missing = [col for col in required if col not in expertise_data.columns]

    if missing:
        raise ValueError(
            f"Missing columns for expertise chart: {missing}"
        )

    if expertise_data.empty:
        return go.Figure().update_layout(
            title="Average Teacher Rating by Expertise",
            template="plotly_dark",
        )

    data = expertise_data.sort_values("AverageTeacherRating")

    error_args = {}
    if "RatingSD" in data.columns:
        error_args["error_x"] = "RatingSD"

    hover_columns = (
        ["InstructorCount"]
        if "InstructorCount" in data.columns
        else None
    )

    fig = px.bar(
        data,
        x="AverageTeacherRating",
        y="Expertise",
        orientation="h",
        hover_data=hover_columns,
        title="Average Teacher Rating by Expertise",
        labels={
            "AverageTeacherRating": "Average Teacher Rating",
            "Expertise": "Instructor Expertise",
        },
        **error_args,
    )

    fig.update_layout(template="plotly_dark", height=480)
    return fig


def category_bar(category_data):
    """Compare average course ratings by category."""
    required = ["AverageCourseRating", "CourseCategory"]
    missing = [col for col in required if col not in category_data.columns]

    if missing:
        raise ValueError(
            f"Missing columns for category chart: {missing}"
        )

    if category_data.empty:
        return go.Figure().update_layout(
            title="Average Course Rating by Category",
            template="plotly_dark",
        )

    data = category_data.sort_values("AverageCourseRating")

    error_args = {}
    if "RatingSD" in data.columns:
        error_args["error_x"] = "RatingSD"

    hover_columns = (
        ["CourseCount"] if "CourseCount" in data.columns else None
    )

    fig = px.bar(
        data,
        x="AverageCourseRating",
        y="CourseCategory",
        orientation="h",
        hover_data=hover_columns,
        title="Average Course Rating by Category",
        labels={
            "AverageCourseRating": "Average Course Rating",
            "CourseCategory": "Course Category",
        },
        **error_args,
    )

    fig.update_layout(
        template="plotly_dark",
        height=480,
        xaxis={"range": [0, 5]},
    )
    return fig


def heatmap_figure(pivot):
    """Display average course ratings by category and course level."""
    if pivot.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Course Rating: Category × Level",
            template="plotly_dark",
        )
        return fig

    figure = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=[str(value) for value in pivot.columns],
            y=[str(value) for value in pivot.index],
            colorbar={"title": "Average rating"},
            zmin=0,
            zmax=5,
            hoverongaps=False,
            colorscale="Viridis",
        )
    )

    figure.update_layout(
        title="Course Rating: Category × Level",
        xaxis_title="Course Level",
        yaxis_title="Course Category",
        template="plotly_dark",
        height=500,
    )

    return figure
