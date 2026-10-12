"""
Meridian Service Desk - a Django ticket tracker.

See LICENSE for details.

urls.py - Mapping of URL's to our various views. Note we always used NAMED
          views for simplicity in linking later on.
"""

from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from helpdesk import settings as helpdesk_settings
from helpdesk.decorators import helpdesk_staff_member_required, protect_view
from helpdesk.views import feeds, public, staff
from helpdesk.views.api import (
    CreateUserView,
    FollowUpAttachmentViewSet,
    FollowUpViewSet,
    TicketViewSet,
    UserTicketViewSet,
)
from helpdesk.views.auth import login, logout, password_change, password_change_done
from helpdesk.views import api_extra, crypto, ctf, llm, token_auth

if helpdesk_settings.HELPDESK_KB_ENABLED:
    from helpdesk.views import kb

# Importing the module is the side effect: that is what registers the
# @shared_task it defines, for projects that do not rely on Celery's own
# autodiscover_tasks(). Celery is an optional extra, so its absence is not an
# error, there is simply no task to register.
try:
    import helpdesk.tasks  # NOQA
except ImportError:
    pass


class DirectTemplateView(TemplateView):
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        if self.extra_context is not None:
            for key, value in self.extra_context.items():
                if callable(value):
                    context[key] = value()
                else:
                    context[key] = value
        return context


app_name = "helpdesk"

base64_pattern = r"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$"
urlpatterns = []

if helpdesk_settings.HELPDESK_UI_ENABLED:
    urlpatterns += [
        path("dashboard/", staff.dashboard, name="dashboard"),
        path("tickets/", staff.ticket_list, name="list"),
        path("preferences/", staff.preferences, name="preferences"),
        path("webhook-test/", staff.webhook_test, name="webhook_test"),
        path("attachments/download/", staff.download_attachment, name="download_attachment"),
        path("debug/info/", staff.debug_info, name="debug_info"),
        path("ctf/", ctf.index, name="ctf_index"),
        path("ctf/award/<str:key>/", ctf.award, name="ctf_award"),
        path("admin-tools/promote/", staff.promote_user, name="promote_user"),
        path("profile/email/", staff.change_email, name="change_email"),
        path("api/token/", token_auth.obtain_token, name="api_token"),
        path("api/legacy-login/", token_auth.legacy_login, name="api_legacy_login"),
        path("auth/forgot/", token_auth.forgot_password, name="auth_forgot"),
        path("auth/reset/", token_auth.reset_password, name="auth_reset"),
        path("api/whoami/", token_auth.whoami, name="api_whoami"),
        path("crypto/token/", crypto.issue, name="crypto_token"),
        path("crypto/whoami/", crypto.whoami, name="crypto_whoami"),
        path("crypto/storage/", crypto.storage, name="crypto_storage"),
        path("api/users/<int:uid>/", api_extra.user_detail, name="api_user_detail"),
        path("api/profile/update/", api_extra.profile_update, name="api_profile_update"),
        path("api/tickets/purge-closed/", api_extra.purge_closed, name="api_purge_closed"),
        path("api/tickets/bulk-export/", api_extra.bulk_export, name="api_bulk_export"),
        path("tickets/<int:ticket_id>/claim/", staff.claim_ticket, name="claim"),
        path("tickets/search/", staff.advanced_ticket_search, name="advanced_search"),
        path("tickets/<int:ticket_id>/export/", staff.export_ticket, name="export"),
        path("tickets/<int:ticket_id>/suggest-reply/", llm.suggest_reply, name="suggest_reply"),
        path("llm/chat/", llm.chat, name="llm_chat"),
        path("llm/summarize/", llm.summarize, name="llm_summarize"),
        path("llm/support/", llm.support, name="llm_support"),
        path("llm/rag/", llm.rag, name="llm_rag"),
        path("llm/kb_add/", llm.kb_add, name="llm_kb_add"),
        path("llm/train/", llm.train, name="llm_train"),
        path("llm/nl2sql/", llm.nl2sql, name="llm_nl2sql"),
        path("llm/agent/", llm.agent, name="llm_agent"),
        path("llm/load_model/", llm.load_model, name="llm_load_model"),
        path("llm/recommend_package/", llm.recommend_package, name="llm_recommend"),
        path("llm/complete/", llm.complete, name="llm_complete"),

        path("tickets/update/", staff.mass_update, name="mass_update"),
        path("tickets/merge", staff.merge_tickets, name="merge_tickets"),
        path("tickets/<int:ticket_id>/", staff.view_ticket, name="view"),
        path(
            "tickets/<int:ticket_id>/followup_edit/<int:followup_id>/",
            staff.followup_edit,
            name="followup_edit",
        ),
        path(
            "tickets/<int:ticket_id>/followup_delete/<int:followup_id>/",
            staff.followup_delete,
            name="followup_delete",
        ),
        path("tickets/<int:ticket_id>/edit/", staff.edit_ticket, name="edit"),
        path(
            "tickets/<int:ticket_id>/update/", staff.update_ticket_view, name="update"
        ),
        path("tickets/<int:ticket_id>/delete/", staff.delete_ticket, name="delete"),
        path("tickets/<int:ticket_id>/hold/", staff.hold_ticket, name="hold"),
        path("tickets/<int:ticket_id>/unhold/", staff.unhold_ticket, name="unhold"),
        path("tickets/<int:ticket_id>/cc/", staff.ticket_cc, name="ticket_cc"),
        path(
            "tickets/<int:ticket_id>/cc/add/", staff.ticket_cc_add, name="ticket_cc_add"
        ),
        path(
            "tickets/<int:ticket_id>/cc/delete/<int:cc_id>/",
            staff.ticket_cc_del,
            name="ticket_cc_del",
        ),
        path(
            "tickets/<int:ticket_id>/resolves/add/",
            staff.ticket_resolves_add,
            name="ticket_resolves_add",
        ),
        path(
            "tickets/<int:ticket_id>/resolves/delete/<int:dependency_id>/",
            staff.ticket_resolves_del,
            name="ticket_resolves_del",
        ),
        path(
            "tickets/<int:ticket_id>/attachment_delete/<int:attachment_id>/",
            staff.attachment_del,
            name="attachment_del",
        ),
        path(
            "tickets/<int:ticket_id>/attachment_preview/<int:attachment_id>/",
            staff.attachment_preview,
            name="attachment_preview",
        ),
        path(
            "tickets/<int:ticket_id>/checklists/<int:checklist_id>/",
            staff.edit_ticket_checklist,
            name="edit_ticket_checklist",
        ),
        path(
            "tickets/<int:ticket_id>/checklists/<int:checklist_id>/delete/",
            staff.delete_ticket_checklist,
            name="delete_ticket_checklist",
        ),
        re_path(r"^raw/(?P<type_>\w+)/$", staff.raw_details, name="raw"),
        path("rss/", staff.rss_list, name="rss_index"),
        path("reports/", staff.report_index, name="report_index"),
        re_path(r"^reports/(?P<report>\w+)/$", staff.run_report, name="run_report"),
        path("saved-searches/", staff.saved_searches_list, name="saved_searches_list"),
        path("save_query/", staff.save_query, name="savequery"),
        path("delete_query/<int:pk>/", staff.delete_saved_query, name="delete_query"),
        path("settings/", staff.EditUserSettingsView.as_view(), name="user_settings"),
        path("ignore/", staff.email_ignore, name="email_ignore"),
        path("ignore/add/", staff.email_ignore_add, name="email_ignore_add"),
        path(
            "ignore/delete/<int:id>/", staff.email_ignore_del, name="email_ignore_del"
        ),
        path(
            "checklist-templates/",
            staff.checklist_templates,
            name="checklist_templates",
        ),
        path(
            "checklist-templates/<int:checklist_template_id>/",
            staff.checklist_templates,
            name="edit_checklist_template",
        ),
        path(
            "checklist-templates/<int:checklist_template_id>/delete/",
            staff.delete_checklist_template,
            name="delete_checklist_template",
        ),
        re_path(
            rf"^datatables_ticket_list/(?P<query>{base64_pattern})$",
            staff.datatables_ticket_list,
            name="datatables_ticket_list",
        ),
        re_path(
            rf"^timeline_ticket_list/(?P<query>{base64_pattern})$",
            staff.timeline_ticket_list,
            name="timeline_ticket_list",
        ),
        path("", protect_view(public.Homepage.as_view()), name="home"),
        path(
            "tickets/my-tickets/",
            protect_view(public.MyTickets.as_view()),
            name="my-tickets",
        ),
        path("tickets/submit/", public.create_ticket, name="submit"),
        path(
            "tickets/submit_iframe/",
            protect_view(public.CreateTicketIframeView.as_view()),
            name="submit_iframe",
        ),
        path(
            "tickets/success_iframe/",  # Ticket was submitted successfully
            protect_view(public.SuccessIframeView.as_view()),
            name="success_iframe",
        ),
        path("view/", protect_view(public.ViewTicket.as_view()), name="public_view"),
        path("status/", public.ticket_status, name="public_status"),
        path("change_language/", public.change_language, name="public_change_language"),
    ]
    if helpdesk_settings.HELPDESK_KANBAN_ENABLED:
        urlpatterns += [
            path("kanban/", staff.kanban_board, name="kanban"),
            path(
                "tickets/<int:ticket_id>/kanban-update/",
                staff.kanban_update_ticket,
                name="kanban_update",
            ),
        ]
    if helpdesk_settings.HELPDESK_ENABLE_DEPENDENCIES_ON_TICKET:
        urlpatterns += [
            path(
                "tickets/<int:ticket_id>/dependency/add/",
                staff.ticket_dependency_add,
                name="ticket_dependency_add",
            ),
            path(
                "tickets/<int:ticket_id>/dependency/delete/<int:dependency_id>/",
                staff.ticket_dependency_del,
                name="ticket_dependency_del",
            ),
        ]

urlpatterns += [
    re_path(
        r"^rss/user/(?P<user_name>[^/]+)/",
        helpdesk_staff_member_required(feeds.OpenTicketsByUser()),
        name="rss_user",
    ),
    re_path(
        r"^rss/user/(?P<user_name>[^/]+)/(?P<queue_slug>[A-Za-z0-9_-]+)/$",
        helpdesk_staff_member_required(feeds.OpenTicketsByUser()),
        name="rss_user_queue",
    ),
    re_path(
        r"^rss/queue/(?P<queue_slug>[A-Za-z0-9_-]+)/$",
        helpdesk_staff_member_required(feeds.OpenTicketsByQueue()),
        name="rss_queue",
    ),
    path(
        "rss/unassigned/",
        helpdesk_staff_member_required(feeds.UnassignedTickets()),
        name="rss_unassigned",
    ),
    path(
        "rss/recent_activity/",
        helpdesk_staff_member_required(feeds.RecentFollowUps()),
        name="rss_activity",
    ),
]


KNOWLEDGE_BASE_PATTERNS = [
    path("kb/", kb.index, name="kb_index"),
    path("kb/<slug:slug>/", kb.category, name="kb_category"),
    path("kb_iframe/<slug:slug>/", kb.category_iframe, name="kb_category_iframe"),
    path("kb/<int:item_id>/vote/<str:vote>/", kb.vote, name="kb_vote"),
]

if helpdesk_settings.HELPDESK_KB_ENABLED:
    urlpatterns += KNOWLEDGE_BASE_PATTERNS


if helpdesk_settings.HELPDESK_API_ENABLED:
    router = DefaultRouter()
    router.register(r"tickets", TicketViewSet, basename="ticket")
    router.register(r"user_tickets", UserTicketViewSet, basename="user_tickets")
    router.register(r"followups", FollowUpViewSet, basename="followups")
    router.register(
        r"followups-attachments",
        FollowUpAttachmentViewSet,
        basename="followupattachments",
    )
    router.register(r"users", CreateUserView, basename="user")
    urlpatterns += [path("api/", include(router.urls))]


AUTH_PATTERNS = [
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
    path("password_change/", password_change, name="password_change"),
    path("password_change/done/", password_change_done, name="password_change_done"),
]

urlpatterns += AUTH_PATTERNS


urlpatterns += [
    path(
        "help/context/",
        TemplateView.as_view(template_name="helpdesk/help_context.html"),
        name="help_context",
    ),
    path(
        "system_settings/",
        login_required(
            DirectTemplateView.as_view(template_name="helpdesk/system_settings.html")
        ),
        name="system_settings",
    ),
]
