.. doctest docs/specs/topics/ddh.rst
.. _welfare.specs.ddh:

=============================
Preventing accidental deletes
=============================

.. contents::
   :depth: 2

.. include:: /../docs/shared/include/tested.rst


>>> import lino
>>> lino.startup('lino_welfare.projects.gerd.settings.doctests')
>>> from lino.api.doctest import *


Foreign Keys and their `on_delete` setting
==========================================

Here is the output of :meth:`lino.utils.diag.Analyzer.show_foreign_keys` in
Lino Welfare:


>>> from lino.utils.diag import analyzer
>>> print(analyzer.show_foreign_keys())
... #doctest: +NORMALIZE_WHITESPACE +REPORT_UDIFF
- accounting.Account :
  - PROTECT : accounting.Journal.account, accounting.MatchRule.account, accounting.Movement.account, finan.BankStatement.item_account, finan.BankStatementItem.account, finan.JournalEntry.item_account, finan.JournalEntryItem.account, finan.PaymentOrder.item_account, finan.PaymentOrderItem.account, vatless.InvoiceItem.account
- accounting.Journal :
  - CASCADE : accounting.MatchRule.journal
  - PROTECT : accounting.Voucher.journal
- accounting.PaymentTerm :
  - PROTECT : vatless.AccountInvoice.payment_term
- accounting.Voucher :
  - CASCADE : accounting.Movement.voucher
  - PROTECT : finan.BankStatement.voucher_ptr, finan.JournalEntry.voucher_ptr, finan.PaymentOrder.voucher_ptr, vatless.AccountInvoice.voucher_ptr
- aids.AidType :
  - PROTECT : aids.Granting.aid_type
- aids.Category :
  - PROTECT : aids.Granting.category, aids.IncomeConfirmation.category
- aids.Granting :
  - PROTECT : aids.IncomeConfirmation.granting, aids.RefundConfirmation.granting, aids.SimpleConfirmation.granting
- art61.ContractType :
  - PROTECT : art61.Contract.type
- b2c.Account :
  - PROTECT : b2c.Statement.account
- b2c.Statement :
  - PROTECT : b2c.Transaction.statement
- boards.Board :
  - PROTECT : aids.AidType.board, aids.Granting.board, boards.Member.board
- cal.Calendar :
  - CASCADE : cal.Subscription.calendar
  - PROTECT : cal.Room.calendar, system.SiteConfig.site_calendar, users.User.calendar
- cal.Event :
  - CASCADE : cal.Guest.event
  - PROTECT : cal.EntryRepeater.cal_entry
- cal.EventType :
  - PROTECT : cal.Event.event_type, cal.EventPolicy.event_type, cal.RecurrentEvent.event_type, isip.ExamPolicy.event_type, system.SiteConfig.client_calendar, system.SiteConfig.default_event_type, system.SiteConfig.prompt_calendar, users.User.event_type
- cal.GuestRole :
  - PROTECT : cal.Guest.role, coachings.CoachingType.eval_guestrole, system.SiteConfig.client_guestrole, system.SiteConfig.team_guestrole, xcourses.CourseOffer.guest_role
- cal.Room :
  - PROTECT : cal.Event.room
- cbss.Purpose :
  - PROTECT : cbss.ManageAccessRequest.purpose
- cbss.Sector :
  - PROTECT : cbss.ManageAccessRequest.sector
- clients.ClientContactType :
  - PROTECT : aids.AidType.pharmacy_type, aids.RefundConfirmation.doctor_type, clients.ClientContact.type, contacts.Partner.client_contact_type
- coachings.CoachingEnding :
  - PROTECT : coachings.Coaching.ending
- coachings.CoachingType :
  - PROTECT : coachings.Coaching.type, coachings.CoachingEnding.type, users.User.coaching_type
- contacts.Company :
  - CASCADE : jobs.JobProvider.company_ptr, xcourses.CourseProvider.company_ptr
  - PROTECT : accounting.Journal.partner, aids.AidType.company, aids.IncomeConfirmation.company, aids.RefundConfirmation.company, aids.RefundConfirmation.pharmacy, aids.SimpleConfirmation.company, art61.Activation.company, cal.Room.company, clients.ClientContact.company, contacts.Role.company, debts.Entry.bailiff, excerpts.Excerpt.company, isip.ContractPartner.company, jobs.Contract.company, notes.Note.company, pcsw.Client.health_insurance, pcsw.Client.pharmacy, uploads.Upload.company
- contacts.CompanyType :
  - PROTECT : contacts.Company.type
- contacts.Partner :
  - CASCADE : addresses.Address.partner, contacts.Company.partner_ptr, contacts.Person.partner_ptr, households.Household.partner_ptr, sepa.Account.partner
  - PROTECT : accounting.Movement.partner, cal.Guest.partner, debts.Actor.partner, debts.Budget.partner, debts.Entry.partner, finan.BankStatementItem.partner, finan.JournalEntryItem.partner, finan.PaymentOrderItem.partner, outbox.Recipient.partner, users.User.partner, vatless.AccountInvoice.partner
- contacts.Person :
  - CASCADE : pcsw.Client.person_ptr
  - PROTECT : aids.AidType.contact_person, aids.IncomeConfirmation.contact_person, aids.RefundConfirmation.contact_person, aids.RefundConfirmation.doctor, aids.SimpleConfirmation.contact_person, art61.Activation.contact_person, art61.Contract.contact_person, art61.Contract.signer1, art61.Contract.signer2, boards.Member.person, cal.Room.contact_person, clients.ClientContact.contact_person, contacts.Role.person, excerpts.Excerpt.contact_person, households.Member.person, humanlinks.Link.child, humanlinks.Link.parent, isip.Contract.signer1, isip.Contract.signer2, isip.ContractPartner.contact_person, jobs.Contract.contact_person, jobs.Contract.signer1, jobs.Contract.signer2, notes.Note.contact_person, system.SiteConfig.signer1, system.SiteConfig.signer2, uploads.Upload.contact_person
- contacts.Role :
  - PROTECT : pcsw.Client.job_office_contact
- contacts.RoleType :
  - PROTECT : aids.AidType.contact_role, aids.IncomeConfirmation.contact_role, aids.RefundConfirmation.contact_role, aids.SimpleConfirmation.contact_role, art61.Activation.contact_role, art61.Contract.contact_role, boards.Member.role, cal.Room.contact_role, clients.ClientContact.contact_role, contacts.Role.type, excerpts.Excerpt.contact_role, isip.ContractPartner.contact_role, jobs.Contract.contact_role, notes.Note.contact_role, system.SiteConfig.signer1_function, system.SiteConfig.signer2_function, uploads.Upload.contact_role
- contenttypes.ContentType :
  - PROTECT : cal.Event.owner_type, cal.Task.owner_type, changes.Change.master_type, changes.Change.object_type, checkdata.Message.owner_type, excerpts.Excerpt.owner_type, excerpts.ExcerptType.content_type, memo.Mention.owner_type, memo.Mention.target_type, notes.Note.owner_type, notify.Message.owner_type, outbox.Attachment.owner_type, outbox.Mail.owner_type, uploads.Upload.owner_type
- countries.Country :
  - PROTECT : addresses.Address.country, contacts.Partner.country, countries.Country.actual_country, countries.Place.country, cv.Experience.country, cv.Study.country, cv.Training.country, pcsw.Client.birth_country, pcsw.Client.nationality
- countries.Place :
  - PROTECT : addresses.Address.city, addresses.Address.region, contacts.Partner.city, contacts.Partner.region, countries.Place.parent, cv.Experience.city, cv.Study.city, cv.Training.city
- cv.Duration :
  - PROTECT : art61.Contract.cv_duration, cv.Experience.duration
- cv.EducationLevel :
  - PROTECT : cv.Study.education_level, cv.StudyType.education_level, esf.ClientSummary.education_level
- cv.Function :
  - PROTECT : art61.Contract.function, cv.Experience.function, cv.Training.function, jobs.Candidature.function, jobs.Job.function, jobs.Offer.function
- cv.Regime :
  - PROTECT : art61.Contract.regime, cv.Experience.regime, jobs.Contract.regime
- cv.Sector :
  - PROTECT : art61.Contract.sector, cv.Experience.sector, cv.Function.sector, cv.Training.sector, jobs.Candidature.sector, jobs.Job.sector, jobs.Offer.sector
- cv.Status :
  - PROTECT : art61.Contract.status, cv.Experience.status
- cv.StudyType :
  - PROTECT : cv.Study.type, cv.Training.type, isip.Contract.study_type
- debts.Account :
  - PROTECT : debts.Entry.account
- debts.Actor :
  - PROTECT : debts.Entry.actor
- debts.Budget :
  - CASCADE : debts.Actor.budget, debts.Entry.budget
  - PROTECT : system.SiteConfig.master_budget
- debts.Group :
  - PROTECT : debts.Account.group
- excerpts.Excerpt :
  - SET_NULL : aids.IncomeConfirmation.printed_by, aids.RefundConfirmation.printed_by, aids.SimpleConfirmation.printed_by, art61.Contract.printed_by, cbss.IdentifyPersonRequest.printed_by, cbss.ManageAccessRequest.printed_by, cbss.RetrieveTIGroupsRequest.printed_by, debts.Budget.printed_by, esf.ClientSummary.printed_by, finan.BankStatement.printed_by, finan.JournalEntry.printed_by, finan.PaymentOrder.printed_by, isip.Contract.printed_by, jobs.Contract.printed_by
- excerpts.ExcerptType :
  - PROTECT : excerpts.Excerpt.excerpt_type
- finan.BankStatement :
  - CASCADE : finan.BankStatementItem.voucher
- finan.JournalEntry :
  - CASCADE : finan.JournalEntryItem.voucher
- finan.PaymentOrder :
  - CASCADE : finan.PaymentOrderItem.voucher
- households.Household :
  - CASCADE : households.Member.household
- households.Type :
  - PROTECT : households.Household.type
- isip.Contract :
  - CASCADE : isip.ContractPartner.contract
- isip.ContractEnding :
  - PROTECT : art61.Contract.ending, isip.Contract.ending, jobs.Contract.ending
- isip.ContractType :
  - PROTECT : isip.Contract.type
- isip.ExamPolicy :
  - PROTECT : art61.Contract.exam_policy, art61.ContractType.exam_policy, isip.Contract.exam_policy, isip.ContractType.exam_policy, jobs.Contract.exam_policy, jobs.ContractType.exam_policy
- jobs.ContractType :
  - PROTECT : jobs.Contract.type, jobs.Job.contract_type
- jobs.Job :
  - PROTECT : jobs.Candidature.job, jobs.Contract.job
- jobs.JobProvider :
  - PROTECT : art61.Contract.company, jobs.Job.provider, jobs.Offer.provider
- jobs.JobType :
  - PROTECT : jobs.Job.type
- jobs.Schedule :
  - PROTECT : jobs.Contract.schedule
- languages.Language :
  - PROTECT : cv.LanguageKnowledge.language, cv.Study.language, cv.Training.language
- newcomers.Broker :
  - PROTECT : pcsw.Client.broker
- newcomers.Faculty :
  - PROTECT : newcomers.Competence.faculty, pcsw.Client.faculty
- notes.EventType :
  - PROTECT : notes.Note.event_type, system.SiteConfig.system_note_type
- notes.NoteType :
  - PROTECT : notes.Note.type
- outbox.Mail :
  - CASCADE : outbox.Attachment.mail, outbox.Recipient.mail
- pcsw.Activity :
  - PROTECT : contacts.Partner.activity
- pcsw.AidType :
  - PROTECT : pcsw.Client.aid_type
- pcsw.Client :
  - CASCADE : aids.IncomeConfirmation.client, aids.RefundConfirmation.client, aids.SimpleConfirmation.client, coachings.Coaching.client, cv.LanguageKnowledge.person, cv.PersonProperty.person, dupable_clients.Word.owner, esf.ClientSummary.master, pcsw.Dispense.client
  - PROTECT : accounting.Movement.project, aids.Granting.client, art61.Activation.client, art61.Contract.client, cal.Event.project, cal.Task.project, cbss.IdentifyPersonRequest.person, cbss.ManageAccessRequest.person, cbss.RetrieveTIGroupsRequest.person, clients.ClientContact.client, cv.Experience.person, cv.Study.person, cv.Training.person, excerpts.Excerpt.project, finan.BankStatementItem.project, finan.JournalEntry.project, finan.JournalEntryItem.project, finan.PaymentOrderItem.project, isip.Contract.client, jobs.Candidature.person, jobs.Contract.client, notes.Note.project, outbox.Mail.project, pcsw.Conviction.client, pcsw.Exclusion.person, uploads.Upload.project, vatless.AccountInvoice.project, vatless.InvoiceItem.project, xcourses.CourseRequest.person
- pcsw.DispenseReason :
  - PROTECT : pcsw.Dispense.reason
- pcsw.ExclusionType :
  - PROTECT : pcsw.Exclusion.type
- pcsw.PersonGroup :
  - PROTECT : pcsw.Client.group
- periods.StoredPeriod :
  - PROTECT : accounting.Voucher.accounting_period
- periods.StoredYear :
  - PROTECT : accounting.Voucher.fiscal_year, periods.StoredPeriod.year
- properties.PropGroup :
  - PROTECT : cv.PersonProperty.group, properties.Property.group
- properties.PropType :
  - PROTECT : properties.PropChoice.type, properties.Property.type
- properties.Property :
  - PROTECT : cv.PersonProperty.property
- sepa.Account :
  - PROTECT : accounting.Journal.sepa_account, finan.PaymentOrderItem.bank_account, vatless.AccountInvoice.bank_account
- uploads.UploadType :
  - PROTECT : uploads.Upload.type
- uploads.Volume :
  - PROTECT : accounting.Journal.uploads_volume, uploads.Upload.volume
- users.User :
  - CASCADE : accounting.LedgerInfo.user, cal.Subscription.user
  - PROTECT : accounting.Voucher.user, aids.Granting.signer, aids.Granting.user, aids.IncomeConfirmation.signer, aids.IncomeConfirmation.user, aids.RefundConfirmation.signer, aids.RefundConfirmation.user, aids.SimpleConfirmation.signer, aids.SimpleConfirmation.user, art61.Activation.user, art61.Contract.user, art61.Contract.user_asd, cal.Event.assigned_to, cal.Event.user, cal.RecurrentEvent.user, cal.Task.user, cbss.IdentifyPersonRequest.user, cbss.ManageAccessRequest.user, cbss.RetrieveTIGroupsRequest.user, changes.Change.user, checkdata.Message.user, coachings.Coaching.user, dashboard.Widget.user, debts.Budget.user, excerpts.Excerpt.user, isip.Contract.user, isip.Contract.user_asd, isip.Contract.user_dsbe, jobs.Contract.user, jobs.Contract.user_asd, newcomers.Competence.user, notes.Note.user, notify.Message.user, outbox.Mail.user, tinymce.TextFieldTemplate.user, uploads.Upload.user, users.Authority.authorized, users.Authority.user
- vatless.AccountInvoice :
  - CASCADE : vatless.InvoiceItem.voucher
- xcourses.Course :
  - PROTECT : xcourses.CourseRequest.course
- xcourses.CourseContent :
  - PROTECT : xcourses.CourseOffer.content, xcourses.CourseRequest.content
- xcourses.CourseOffer :
  - PROTECT : xcourses.Course.offer, xcourses.CourseRequest.offer
- xcourses.CourseProvider :
  - PROTECT : xcourses.CourseOffer.provider
<BLANKLINE>


Users and partners
==================

It is not allowed to delete a person who is being used as the
:attr:`partner <lino.modlib.users.models.User.partner>` of a user
(although that field is nullable).

>>> rt.show('users.AllUsers', column_names="id username partner partner__id",
...     language="en")
==== ========== ================= ====
 ID   Username   Partner           ID
---- ---------- ----------------- ----
 6    alicia     Allmanns Alicia   85
 9    caroline
 5    hubert     Huppertz Hubert   84
 10   judith     Jousten Judith    87
 13   kerstin
 4    melanie    Mélard Mélanie    83
 8    nicolas
 11   patrick
 3    robin
 1    rolf
 2    romain
 7    theresia   Thelen Theresia   86
 12   wilfried
==== ========== ================= ====
<BLANKLINE>

The message is the same whether you try on the Person or on the Partner:


>>> obj = contacts.Person.objects.get(id=85)
>>> with translation.override('en'):
...     print(obj.disable_delete())  #doctest: +NORMALIZE_WHITESPACE
Cannot delete Partner Allmanns Alicia because 45 Presences refer to it.
(<QuerySet [Guest #20 ('Presence #20 (29.10.2012 09:00)'), Guest #22 ('Presence
#22 (29.11.2012 09:00)'), Guest #24 ('Presence #24 (31.12.2012 09:00)'), Guest
#26 ('Presence #26 (31.01.2013 09:00)'), Guest #28 ('Presence #28 (28.02.2013
09:00)'), Guest #30 ('Presence #30 (28.03.2013 09:00)'), Guest #32 ('Presence
#32 (29.04.2013 09:00)'), Guest #34 ('Presence #34 (29.05.2013 09:00)'), Guest
#36 ('Presence #36 (01.07.2013 09:00)'), Guest #38 ('Presence #38 (01.08.2013
09:00)'), Guest #40 ('Presence #40 (09.09.2013 09:00)'), Guest #42 ('Presence
#42 (09.10.2013 09:00)'), Guest #44 ('Presence #44 (12.11.2013 09:00)'), Guest
#46 ('Presence #46 (12.12.2013 09:00)'), Guest #48 ('Presence #48 (13.01.2014
09:00)'), Guest #50 ('Presence #50 (13.02.2014 09:00)'), Guest #52 ('Presence
#52 (13.03.2014 09:00)'), Guest #54 ('Presence #54 (14.04.2014 09:00)'), Guest
#56 ('Presence #56 (14.05.2014 09:00)'), Guest #58 ('Presence #58 (16.06.2014
09:00)'), '...(remaining elements truncated)...']> via partner)


>>> with translation.override('en'):
...     print(obj.disable_delete())  #doctest: +NORMALIZE_WHITESPACE
Cannot delete Partner Allmanns Alicia because 45 Presences refer to it.
(<QuerySet [Guest #20 ('Presence #20 (29.10.2012 09:00)'), Guest #22 ('Presence
#22 (29.11.2012 09:00)'), Guest #24 ('Presence #24 (31.12.2012 09:00)'), Guest
#26 ('Presence #26 (31.01.2013 09:00)'), Guest #28 ('Presence #28 (28.02.2013
09:00)'), Guest #30 ('Presence #30 (28.03.2013 09:00)'), Guest #32 ('Presence
#32 (29.04.2013 09:00)'), Guest #34 ('Presence #34 (29.05.2013 09:00)'), Guest
#36 ('Presence #36 (01.07.2013 09:00)'), Guest #38 ('Presence #38 (01.08.2013
09:00)'), Guest #40 ('Presence #40 (09.09.2013 09:00)'), Guest #42 ('Presence
#42 (09.10.2013 09:00)'), Guest #44 ('Presence #44 (12.11.2013 09:00)'), Guest
#46 ('Presence #46 (12.12.2013 09:00)'), Guest #48 ('Presence #48 (13.01.2014
09:00)'), Guest #50 ('Presence #50 (13.02.2014 09:00)'), Guest #52 ('Presence
#52 (13.03.2014 09:00)'), Guest #54 ('Presence #54 (14.04.2014 09:00)'), Guest
#56 ('Presence #56 (14.05.2014 09:00)'), Guest #58 ('Presence #58 (16.06.2014
09:00)'), '...(remaining elements truncated)...']> via partner)

You also can't delete a partner when a person or some other MTI child is being
referred to by other objects:

>>> obj = contacts.Partner.objects.get(id=91)
>>> with translation.override('en'):
...     print(obj.disable_delete())  #doctest: +NORMALIZE_WHITESPACE
Cannot delete Partner Die neue Alternative V.o.G. because 2 Budget Entries refer
to it. (<QuerySet [Entry #765 ('Row # 49'), Entry #816 ('Row # 55')]> via
partner)
