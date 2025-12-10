# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AccountOtp(models.Model):
    created_at = models.DateTimeField()
    is_used = models.BooleanField()
    otp_type = models.CharField(max_length=20)
    user = models.ForeignKey('AccountUser', models.DO_NOTHING)
    code = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'account_otp'


class AccountUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=254)
    location = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField()
    is_staff = models.BooleanField()
    phone = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'account_user'


class AccountUserGroups(models.Model):
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)
    group = models.ForeignKey('AuthGroup', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_user_groups'
        unique_together = (('user', 'group'),)


class AccountUserUserPermissions(models.Model):
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_user_user_permissions'
        unique_together = (('user', 'permission'),)


class ActivitiesActivity(models.Model):
    name = models.CharField(max_length=100)
    system_name = models.CharField(unique=True, max_length=50)
    points_value = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'activities_activity'


class ActivitiesActivitylog(models.Model):
    completion_time = models.DateTimeField()
    activity = models.ForeignKey(ActivitiesActivity, models.DO_NOTHING)
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'activities_activitylog'
        unique_together = (('user', 'activity'),)


class ActivityActivity(models.Model):
    is_once_only = models.BooleanField()
    name = models.CharField(max_length=255)
    system_name = models.CharField(unique=True, max_length=50)
    points_value = models.IntegerField()
    interaction_type = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'activity_activity'


class ActivityActivitylog(models.Model):
    points_awarded = models.IntegerField()
    created_at = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    activity = models.ForeignKey(ActivityActivity, models.DO_NOTHING)
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'activity_activitylog'


class AdoptionAdoptionpost(models.Model):
    created_at = models.DateTimeField()
    owner_message = models.TextField()
    pet = models.OneToOneField('PetsPet', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'adoption_adoptionpost'


class AlertsAlert(models.Model):
    name = models.CharField(max_length=100)
    time = models.TimeField()
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    owner = models.ForeignKey(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'alerts_alert'


class AppointmentAppointment(models.Model):
    service = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    provider = models.CharField(max_length=255)
    pet = models.ForeignKey('PetsPet', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'appointment_appointment'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class DjangoAdminLog(models.Model):
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)
    action_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class MatingMatingpost(models.Model):
    created_at = models.DateTimeField()
    is_active = models.BooleanField()
    owner_message = models.TextField()
    pet = models.OneToOneField('PetsPet', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'mating_matingpost'


class MoodMood(models.Model):
    mood = models.IntegerField()
    pet = models.ForeignKey('PetsPet', models.DO_NOTHING)
    date = models.DateField()

    class Meta:
        managed = False
        db_table = 'mood_mood'


class NotificationsPushtoken(models.Model):
    token = models.CharField(unique=True, max_length=255)
    platform = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'notifications_pushtoken'
        unique_together = (('user', 'token'),)


class PetsPet(models.Model):
    pet_name = models.CharField(max_length=100)
    pet_type = models.CharField(max_length=50)
    pet_color = models.CharField(max_length=50)
    pet_gender = models.CharField(max_length=20)
    pet_birthday = models.DateField()
    owner = models.ForeignKey(AccountUser, models.DO_NOTHING)
    pet_photo = models.CharField(max_length=500, blank=True, null=True)
    qr_token = models.CharField(unique=True, max_length=100, blank=True, null=True)
    qr_url = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pets_pet'


class RequestsInteractionrequest(models.Model):
    request_type = models.CharField(max_length=10)
    message = models.TextField()
    status = models.CharField(max_length=10)
    created_at = models.DateTimeField()
    pet = models.ForeignKey(PetsPet, models.DO_NOTHING)
    receiver = models.ForeignKey(AccountUser, models.DO_NOTHING)
    sender = models.ForeignKey(AccountUser, models.DO_NOTHING, related_name='requestsinteractionrequest_sender_set')
    owner_response_message = models.TextField(blank=True, null=True)
    attached_file = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'requests_interactionrequest'


class RewardAppRedeemlog(models.Model):
    points_deducted = models.IntegerField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    details = models.TextField(blank=True, null=True)
    reward = models.ForeignKey(ActivityActivity, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'reward_app_redeemlog'


class RewardAppRewardcoupon(models.Model):
    code = models.CharField(unique=True, max_length=32)
    is_used = models.BooleanField()
    created_at = models.DateTimeField()
    reward = models.ForeignKey(ActivityActivity, models.DO_NOTHING)
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'reward_app_rewardcoupon'


class RewardAppUserwallet(models.Model):
    total_points = models.IntegerField()
    last_updated = models.DateTimeField()
    user = models.OneToOneField(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'reward_app_userwallet'


class RewardsPointstransaction(models.Model):
    event_type = models.CharField(max_length=50)
    reference = models.CharField(max_length=200, blank=True, null=True)
    amount = models.IntegerField()
    created_at = models.DateTimeField()
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'rewards_pointstransaction'


class RewardsRedeemedreward(models.Model):
    redeemed_at = models.DateTimeField()
    reward = models.ForeignKey('RewardsReward', models.DO_NOTHING)
    user = models.ForeignKey(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'rewards_redeemedreward'


class RewardsReward(models.Model):
    is_active = models.BooleanField()
    description = models.TextField()
    title = models.CharField(max_length=100)
    points_required = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = 'rewards_reward'


class RewardsUserpoints(models.Model):
    balance = models.IntegerField()
    user = models.OneToOneField(AccountUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'rewards_userpoints'


class VaccinationVaccination(models.Model):
    vacc_name = models.CharField(max_length=100)
    vacc_date = models.DateField()
    pet = models.ForeignKey(PetsPet, models.DO_NOTHING)
    vacc_certificate = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vaccination_vaccination'
