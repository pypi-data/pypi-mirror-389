"""
Team Seats Management
Handle team member invitations and seat allocation
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from supabase import create_client, Client
import secrets

logger = logging.getLogger(__name__)

class SeatsManager:
    """Manage team member seats for Team plan subscriptions"""

    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL or SUPABASE_KEY not set")
            self.supabase = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)

    async def get_subscription_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user's subscription"""
        if not self.supabase:
            return None

        try:
            response = self.supabase.table('user_subscriptions') \
                .select('*') \
                .eq('email', email) \
                .eq('status', 'active') \
                .single() \
                .execute()

            return response.data if response.data else None

        except Exception as e:
            logger.error(f"Failed to get subscription: {str(e)}")
            return None

    async def get_team_members(self, subscription_id: str) -> List[Dict[str, Any]]:
        """
        Get all team members for a subscription.

        Args:
            subscription_id: Subscription UUID

        Returns:
            List of team member records
        """
        if not self.supabase:
            return []

        try:
            response = self.supabase.table('team_members') \
                .select('*') \
                .eq('subscription_id', subscription_id) \
                .order('invited_at', desc=True) \
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Failed to get team members: {str(e)}")
            return []

    async def invite_team_member(
        self,
        owner_email: str,
        member_email: str,
        role: str = "member"
    ) -> Dict[str, Any]:
        """
        Invite a new team member.

        Args:
            owner_email: Email of team owner/admin
            member_email: Email of member to invite
            role: Role for the member (admin, member)

        Returns:
            {
                "success": bool,
                "message": str,
                "invitation_id": str (optional)
            }
        """
        if not self.supabase:
            return {"success": False, "message": "Database not available"}

        # Get owner's subscription
        subscription = await self.get_subscription_by_email(owner_email)

        if not subscription:
            return {"success": False, "message": "No active subscription found"}

        # Check if subscription is Team plan
        if subscription['tier'] not in ['team', 'enterprise']:
            return {"success": False, "message": "Team seats only available on Team plan"}

        # Check seats availability
        seats_limit = subscription.get('seats_limit', 1)
        seats_used = subscription.get('seats_used', 1)

        if seats_used >= seats_limit:
            return {
                "success": False,
                "message": f"All {seats_limit} seats are occupied. Upgrade to add more members."
            }

        # Check if member already invited
        existing_members = await self.get_team_members(subscription['id'])
        for member in existing_members:
            if member['email'] == member_email:
                return {"success": False, "message": "User already invited"}

        try:
            # Create team member invitation
            invitation = self.supabase.table('team_members').insert({
                'subscription_id': subscription['id'],
                'email': member_email,
                'role': role,
                'invited_by': owner_email,
                'invited_at': datetime.utcnow().isoformat()
            }).execute()

            # Increment seats_used
            self.supabase.table('user_subscriptions').update({
                'seats_used': seats_used + 1,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', subscription['id']).execute()

            logger.info(f"✅ Invited {member_email} to team (seats: {seats_used + 1}/{seats_limit})")

            return {
                "success": True,
                "message": f"Invitation sent to {member_email}",
                "invitation_id": invitation.data[0]['id'] if invitation.data else None,
                "seats_used": seats_used + 1,
                "seats_limit": seats_limit
            }

        except Exception as e:
            logger.error(f"Failed to invite team member: {str(e)}")
            return {"success": False, "message": f"Failed to send invitation: {str(e)}"}

    async def accept_invitation(self, member_email: str, user_id: str) -> Dict[str, Any]:
        """
        Accept team invitation.

        Args:
            member_email: Email of invited member
            user_id: User ID from authentication

        Returns:
            {
                "success": bool,
                "message": str,
                "subscription": dict (optional)
            }
        """
        if not self.supabase:
            return {"success": False, "message": "Database not available"}

        try:
            # Find pending invitation
            invitation = self.supabase.table('team_members') \
                .select('*') \
                .eq('email', member_email) \
                .is_('joined_at', 'null') \
                .single() \
                .execute()

            if not invitation.data:
                return {"success": False, "message": "No pending invitation found"}

            # Mark invitation as accepted
            self.supabase.table('team_members').update({
                'user_id': user_id,
                'joined_at': datetime.utcnow().isoformat()
            }).eq('id', invitation.data['id']).execute()

            # Get subscription details
            subscription = self.supabase.table('user_subscriptions') \
                .select('*') \
                .eq('id', invitation.data['subscription_id']) \
                .single() \
                .execute()

            logger.info(f"✅ {member_email} accepted team invitation")

            return {
                "success": True,
                "message": "Welcome to the team!",
                "subscription": subscription.data if subscription.data else None
            }

        except Exception as e:
            logger.error(f"Failed to accept invitation: {str(e)}")
            return {"success": False, "message": f"Failed to accept invitation: {str(e)}"}

    async def remove_team_member(
        self,
        owner_email: str,
        member_email: str
    ) -> Dict[str, Any]:
        """
        Remove a team member.

        Args:
            owner_email: Email of team owner/admin
            member_email: Email of member to remove

        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        if not self.supabase:
            return {"success": False, "message": "Database not available"}

        # Get owner's subscription
        subscription = await self.get_subscription_by_email(owner_email)

        if not subscription:
            return {"success": False, "message": "No active subscription found"}

        try:
            # Find team member
            member = self.supabase.table('team_members') \
                .select('*') \
                .eq('subscription_id', subscription['id']) \
                .eq('email', member_email) \
                .single() \
                .execute()

            if not member.data:
                return {"success": False, "message": "Team member not found"}

            # Cannot remove owner
            if member.data['role'] == 'owner':
                return {"success": False, "message": "Cannot remove team owner"}

            # Delete team member
            self.supabase.table('team_members').delete() \
                .eq('id', member.data['id']) \
                .execute()

            # Decrement seats_used
            seats_used = subscription.get('seats_used', 1)
            self.supabase.table('user_subscriptions').update({
                'seats_used': max(1, seats_used - 1),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', subscription['id']).execute()

            logger.info(f"✅ Removed {member_email} from team")

            return {
                "success": True,
                "message": f"Removed {member_email} from team",
                "seats_used": max(1, seats_used - 1)
            }

        except Exception as e:
            logger.error(f"Failed to remove team member: {str(e)}")
            return {"success": False, "message": f"Failed to remove member: {str(e)}"}

    async def update_member_role(
        self,
        owner_email: str,
        member_email: str,
        new_role: str
    ) -> Dict[str, Any]:
        """
        Update team member's role.

        Args:
            owner_email: Email of team owner
            member_email: Email of member to update
            new_role: New role (admin, member)

        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        if not self.supabase:
            return {"success": False, "message": "Database not available"}

        if new_role not in ['admin', 'member']:
            return {"success": False, "message": "Invalid role"}

        # Get owner's subscription
        subscription = await self.get_subscription_by_email(owner_email)

        if not subscription:
            return {"success": False, "message": "No active subscription found"}

        try:
            # Update member role
            self.supabase.table('team_members').update({
                'role': new_role,
            }).eq('subscription_id', subscription['id']) \
              .eq('email', member_email) \
              .execute()

            logger.info(f"✅ Updated {member_email} role to {new_role}")

            return {
                "success": True,
                "message": f"Updated {member_email} to {new_role}"
            }

        except Exception as e:
            logger.error(f"Failed to update role: {str(e)}")
            return {"success": False, "message": f"Failed to update role: {str(e)}"}

    async def get_team_usage_stats(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get team usage statistics.

        Args:
            subscription_id: Subscription UUID

        Returns:
            {
                "total_scans": int,
                "scans_by_member": [{email, scans, last_scan}],
                "top_scanners": [...],
                "seats_used": int,
                "seats_limit": int
            }
        """
        if not self.supabase:
            return {}

        try:
            # Get subscription
            subscription = self.supabase.table('user_subscriptions') \
                .select('*') \
                .eq('id', subscription_id) \
                .single() \
                .execute()

            if not subscription.data:
                return {}

            # Get all scans
            scans = self.supabase.table('scan_usage') \
                .select('*') \
                .eq('subscription_id', subscription_id) \
                .execute()

            # Aggregate by member
            member_stats = {}
            for scan in (scans.data or []):
                user_id = scan.get('user_id')
                if user_id not in member_stats:
                    member_stats[user_id] = {
                        "scans": 0,
                        "last_scan": None
                    }
                member_stats[user_id]["scans"] += 1
                if not member_stats[user_id]["last_scan"] or scan['created_at'] > member_stats[user_id]["last_scan"]:
                    member_stats[user_id]["last_scan"] = scan['created_at']

            # Sort by scans
            top_scanners = sorted(
                [{"user_id": k, **v} for k, v in member_stats.items()],
                key=lambda x: x["scans"],
                reverse=True
            )[:5]

            return {
                "total_scans": subscription.data.get('scans_used', 0),
                "scans_by_member": [{"user_id": k, **v} for k, v in member_stats.items()],
                "top_scanners": top_scanners,
                "seats_used": subscription.data.get('seats_used', 1),
                "seats_limit": subscription.data.get('seats_limit', 1)
            }

        except Exception as e:
            logger.error(f"Failed to get team stats: {str(e)}")
            return {}
