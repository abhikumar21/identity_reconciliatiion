from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Contact


class IdentifyView(APIView):
    def post(self, request):
        email = request.data.get('email')
        phoneNumber = request.data.get('phoneNumber')

        if not email and not phoneNumber:
            return Response({"error": "At least one of email or phoneNumber is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Fetch contacts directly matching email or phone
        initial_contacts = list(Contact.objects.filter(
            Q(email=email) | Q(phoneNumber=phoneNumber)
        ))

        # Step 2: Explore all transitive linked contacts
        all_contacts = set(initial_contacts)
        queue = list(initial_contacts)

        while queue:
            current = queue.pop()
            linked_contacts = Contact.objects.filter(
                Q(linkedId=current.id) | Q(id=current.linkedId_id)
            )
            for contact in linked_contacts:
                if contact not in all_contacts:
                    all_contacts.add(contact)
                    queue.append(contact)

        # Step 3: Identify the primary contact (earliest creation time among primaries)
        if not all_contacts:
            # No existing contact found — create a new primary
            primary = Contact.objects.create(
                email=email,
                phoneNumber=phoneNumber,
                linkPrecedence='primary'
            )
            all_contacts = {primary}
        else:
            primary_contacts = [c for c in all_contacts if c.linkPrecedence == 'primary']
            if primary_contacts:
                primary = min(primary_contacts, key=lambda c: c.createdAt)
            else:
                primary = min(all_contacts, key=lambda c: c.createdAt)
                primary.linkPrecedence = 'primary'
                primary.linkedId = None
                primary.save()


        # Step 4: Convert others to secondary
        for contact in all_contacts:
            if contact.id != primary.id and (contact.linkPrecedence != 'secondary' or contact.linkedId_id != primary.id):
                contact.linkPrecedence = 'secondary'
                contact.linkedId = primary
                contact.save()

        # Step 5: If this email/phone is new, create a new secondary
        emails = set(c.email for c in all_contacts if c.email)
        phones = set(c.phoneNumber for c in all_contacts if c.phoneNumber)

        if (email and email not in emails) or (phoneNumber and phoneNumber not in phones):
            new_contact = Contact.objects.create(
                email=email,
                phoneNumber=phoneNumber,
                linkedId=primary,
                linkPrecedence='secondary'
            )
            all_contacts.add(new_contact)

        # Step 6: Build response
        emails = list(set(c.email for c in all_contacts if c.email))
        phones = list(set(c.phoneNumber for c in all_contacts if c.phoneNumber))
        secondary_ids = [c.id for c in all_contacts if c.linkPrecedence == 'secondary']

        return Response({
            "contact": {
                "primaryContatctId": primary.id,
                "emails": emails,
                "phoneNumbers": phones,
                "secondaryContactIds": secondary_ids
            }
        }, status=status.HTTP_200_OK)
