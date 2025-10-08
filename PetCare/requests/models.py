from django.db import models
from django.contrib.auth import get_user_model
# Assuming the Pet model is in the 'pet' app
from pets.models import Pet 

# Get the custom User model defined in your 'account' app
User = get_user_model()

class InteractionRequest(models.Model):
    """
    Represents a Mating or Adoption request sent from one user to a pet owner.
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

    # Sender (The user initiating the request)
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_requests',
        verbose_name="Sender"
    )
    # The specific Pet being requested
    pet = models.ForeignKey(
        Pet, 
        on_delete=models.CASCADE, 
        related_name='received_requests',
        verbose_name="Requested Pet"
    )
    # Receiver (The Pet's owner)
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
    
    # FileField for the attached file (image, document, etc.)
    attached_file = models.FileField(
        upload_to='request_attachments/', 
        blank=True, 
        null=True
    )
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='Pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Interaction Request"
        verbose_name_plural = "Interaction Requests"

    def __str__(self):
        return f"Request for {self.pet.pet_name} ({self.request_type}) by {self.sender.username}"

# NOTE: You will need to run 'python manage.py makemigrations' and 'python manage.py migrate'
# after adding this model.
