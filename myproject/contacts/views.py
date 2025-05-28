from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Contact
from .serializers import ContactSerializer

class IdentifyView(APIView):
    def post(self, request):
        email = request.data.get('email')
        phoneNumber = request.data.get('phoneNumber')

        if not email and not phoneNumber:
            return Response({"error": "At least one of email or phoneNumber is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch contacts matching email or phoneNumber
        contacts = Contact.objects.filter(
            Q(email=email) | Q(phoneNumber=phoneNumber)
        )

        if contacts.exists():
            # Build a set of all related contacts
            related_contacts = set(contacts)
            for contact in contacts:
                if contact.linkedId:
                    related_contacts.update(Contact.objects.filter(Q(id=contact.linkedId) | Q(linkedId=contact.linkedId)))
                else:
                    related_contacts.update(Contact.objects.filter(linkedId=contact.id))

            # Determine primary contact
            primary_contact = min(
                [c for c in related_contacts if c.linkPrecedence == 'primary'],
                key=lambda x: x.createdAt,
                default=None
            )

            if not primary_contact:
                primary_contact = min(related_contacts, key=lambda x: x.createdAt)
                primary_contact.linkPrecedence = 'primary'
                primary_contact.linkedId = None
                primary_contact.save()

            # Update other contacts to secondary
            for contact in related_contacts:
                if contact.id != primary_contact.id and contact.linkPrecedence != 'secondary':
                    contact.linkPrecedence = 'secondary'
                    contact.linkedId = primary_contact
                    contact.save()

            # If new info, create secondary contact
            existing_emails = {c.email for c in related_contacts if c.email}
            existing_phones = {c.phoneNumber for c in related_contacts if c.phoneNumber}

            if (email and email not in existing_emails) or (phoneNumber and phoneNumber not in existing_phones):
                new_contact = Contact.objects.create(
                    email=email,
                    phoneNumber=phoneNumber,
                    linkedId=primary_contact,
                    linkPrecedence='secondary'
                )
                related_contacts.add(new_contact)

            # Prepare response
            emails = list({c.email for c in related_contacts if c.email})
            phoneNumbers = list({c.phoneNumber for c in related_contacts if c.phoneNumber})
            secondaryContactIds = [c.id for c in related_contacts if c.linkPrecedence == 'secondary']

            return Response({
                "contact": {
                    "primaryContatctId": primary_contact.id,
                    "emails": emails,
                    "phoneNumbers": phoneNumbers,
                    "secondaryContactIds": secondaryContactIds
                }
            }, status=status.HTTP_200_OK)

        else:
            # Create new primary contact
            new_contact = Contact.objects.create(
                email=email,
                phoneNumber=phoneNumber,
                linkPrecedence='primary'
            )
            return Response({
                "contact": {
                    "primaryContatctId": new_contact.id,
                    "emails": [email] if email else [],
                    "phoneNumbers": [phoneNumber] if phoneNumber else [],
                    "secondaryContactIds": []
                }
            }, status=status.HTTP_200_OK)
