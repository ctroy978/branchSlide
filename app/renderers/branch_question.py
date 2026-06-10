from app.models import Branch
from app.renderers.markdown import render_markdown


def render_branch_question(node, branches: list[Branch]) -> str:
    parts: list[str] = []
    if node.branch_question_md.strip():
        parts.append(render_markdown(node.branch_question_md))

    if branches:
        items = []
        for index, branch in enumerate(branches, start=1):
            label = branch.student_label.strip() or branch.label
            items.append(
                f'<li class="branch-option flex items-start gap-4 py-3">'
                f'<span class="branch-number flex-shrink-0 w-8 h-8 rounded-full '
                f'bg-indigo-500/20 text-indigo-300 flex items-center justify-center '
                f'font-semibold text-sm">{index}</span>'
                f'<span class="text-lg leading-snug">{label}</span>'
                f"</li>"
            )
        parts.append(
            '<div class="branch-options mt-8 pt-6 border-t border-slate-600">'
            '<p class="text-sm uppercase tracking-widest text-slate-400 mb-4">'
            "Paths to explore</p>"
            f'<ul class="branch-options-list space-y-1 text-left">{"".join(items)}</ul>'
            "</div>"
        )

    return "\n".join(parts)