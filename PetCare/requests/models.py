from django.db import models
from django.contrib.auth import get_user_model
from pets.models import Pet 

# الحصول على نموذج المستخدم المخصص
User = get_user_model()

class InteractionRequest(models.Model):
    """
    يمثل طلب تزاوج أو تبني مُرسل من مستخدم إلى مالك حيوان أليف.
    """
    INTERACTION_CHOICES = (
        ('Mate', 'Mating Request'),
        ('Adoption', 'Adoption Request'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    )

    # المُرسِل (من أنشأ الطلب)
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_requests',
        verbose_name="Sender"
    )
    # الحيوان الأليف المطلوب
    pet = models.ForeignKey(
        Pet, 
        on_delete=models.CASCADE, 
        related_name='received_requests',
        verbose_name="Requested Pet"
    )
    # المُستقبِل (مالك الحيوان الأليف)
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_requests_as_owner',
        verbose_name="Receiver (Owner)"
    )
    
    request_type = models.CharField(
        max_length=10, 
        choices=INTERACTION_CHOICES,
        default='Adoption'
    )
    message = models.TextField(verbose_name="Request Message")
    
    attached_file = models.CharField( 
        max_length=500, 
        blank=True, 
        null=True
    )
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='Pending'
    )
    
    owner_response_message = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Owner Response Message",
        help_text="الرسالة الاختيارية من المالك عند قبول أو رفض الطلب."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Interaction Request"
        verbose_name_plural = "Interaction Requests"

    def __str__(self):
        sender_name = getattr(self.sender, 'full_name', self.sender.email)
        return f"Request for {self.pet.pet_name} ({self.request_type}) by {sender_name}"