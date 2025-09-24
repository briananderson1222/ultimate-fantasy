"""
Content moderation service.

Provides comprehensive content moderation including:
- Automated content filtering and spam detection
- Profanity filtering and sentiment analysis
- User behavior monitoring and reputation scoring
- Automated actions and escalation workflows
- Manual review queue and admin tools
"""

import asyncio
import re
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, update

try:
    from infrastructure.cache.redis_pool import get_redis_pool
except ImportError:
    get_redis_pool = None

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger

logger = get_logger(__name__)


class ModerationAction(Enum):
    """Content moderation actions."""
    ALLOW = "allow"
    FLAG = "flag"
    WARN = "warn"
    BLOCK = "block"
    BAN_USER = "ban_user"
    ESCALATE = "escalate"


class ViolationType(Enum):
    """Content violation types."""
    PROFANITY = "profanity"
    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    PERSONAL_INFO = "personal_info"
    EXCESSIVE_CAPS = "excessive_caps"
    REPEATED_CONTENT = "repeated_content"
    RATE_LIMITING = "rate_limiting"


class UserStatus(Enum):
    """User moderation status."""
    GOOD_STANDING = "good_standing"
    WARNING = "warning"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    BANNED = "banned"


@dataclass
class ModerationRule:
    """Content moderation rule."""
    rule_id: str
    name: str
    violation_type: ViolationType
    pattern: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    action: ModerationAction = ModerationAction.FLAG
    severity: int = 1  # 1-10 scale
    enabled: bool = True
    auto_apply: bool = True


@dataclass
class ModerationResult:
    """Result of content moderation."""
    action: ModerationAction
    confidence: float
    violations: List[ViolationType]
    severity_score: int
    message: Optional[str] = None
    suggested_action: Optional[ModerationAction] = None
    requires_review: bool = False


@dataclass
class UserReputation:
    """User reputation and behavior metrics."""
    user_id: str
    reputation_score: int = 100
    total_messages: int = 0
    flagged_messages: int = 0
    warnings_received: int = 0
    status: UserStatus = UserStatus.GOOD_STANDING
    last_violation: Optional[datetime] = None
    suspension_until: Optional[datetime] = None
    trust_level: int = 1  # 1-5 scale


@dataclass
class ModerationCase:
    """Moderation case for review."""
    case_id: str
    user_id: str
    content: str
    violation_type: ViolationType
    severity_score: int
    auto_action: ModerationAction
    status: str = "pending"  # pending, reviewed, resolved
    created_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    final_action: Optional[ModerationAction] = None
    notes: Optional[str] = None


class ContentModerationService:
    """
    Comprehensive content moderation service.

    Features:
    - Real-time content filtering and analysis
    - Automated spam and abuse detection
    - User reputation and behavior tracking
    - Escalation workflows for manual review
    - Customizable moderation rules and policies
    """

    def __init__(self, db_session: AsyncSession, redis_pool=None):
        self.db_session = db_session
        self.redis_pool = redis_pool

        # Moderation rules
        self.rules: List[ModerationRule] = []

        # Built-in profanity filter
        self.profanity_words = self._load_profanity_list()
        self.spam_patterns = self._load_spam_patterns()

        # User reputation tracking
        self.user_reputations: Dict[str, UserReputation] = {}

        # Rate limiting thresholds
        self.rate_limits = {
            "messages_per_minute": 10,
            "messages_per_hour": 100,
            "duplicate_threshold": 3,
            "caps_percentage": 70
        }

        self._initialized = False

    async def initialize(self):
        """Initialize moderation service."""
        if self._initialized:
            return

        # Load moderation rules
        await self._load_moderation_rules()

        # Load user reputations from cache
        await self._load_user_reputations()

        self._initialized = True
        logger.info("Content moderation service initialized")

    async def moderate_content(
        self,
        content: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ModerationResult:
        """
        Moderate content and determine appropriate action.

        Args:
            content: Content to moderate
            user_id: User who created the content
            context: Additional context (league_id, message_type, etc.)

        Returns:
            ModerationResult with action and details
        """
        await self.initialize()

        violations = []
        severity_score = 0
        confidence = 1.0

        # Get user reputation
        user_rep = await self._get_user_reputation(user_id)

        # Check profanity
        profanity_result = self._check_profanity(content)
        if profanity_result["has_profanity"]:
            violations.append(ViolationType.PROFANITY)
            severity_score += profanity_result["severity"]

        # Check spam patterns
        spam_result = await self._check_spam(content, user_id, context)
        if spam_result["is_spam"]:
            violations.append(ViolationType.SPAM)
            severity_score += spam_result["severity"]

        # Check excessive caps
        caps_result = self._check_excessive_caps(content)
        if caps_result["excessive"]:
            violations.append(ViolationType.EXCESSIVE_CAPS)
            severity_score += caps_result["severity"]

        # Check for repeated content
        repeat_result = await self._check_repeated_content(content, user_id)
        if repeat_result["is_repeated"]:
            violations.append(ViolationType.REPEATED_CONTENT)
            severity_score += repeat_result["severity"]

        # Check rate limiting
        rate_result = await self._check_rate_limiting(user_id)
        if rate_result["rate_limited"]:
            violations.append(ViolationType.RATE_LIMITING)
            severity_score += rate_result["severity"]

        # Apply custom rules
        custom_violations = await self._apply_custom_rules(content, context)
        violations.extend(custom_violations)

        # Determine action based on violations and user reputation
        action = self._determine_action(violations, severity_score, user_rep)

        # Create moderation result
        result = ModerationResult(
            action=action,
            confidence=confidence,
            violations=violations,
            severity_score=severity_score,
            requires_review=severity_score >= 7 or user_rep.status != UserStatus.GOOD_STANDING
        )

        # Update user reputation
        await self._update_user_reputation(user_id, violations, severity_score)

        # Create moderation case if needed
        if result.requires_review:
            await self._create_moderation_case(user_id, content, violations, severity_score, action)

        # Log moderation action
        logger.info(
            f"Content moderated for user {user_id}: "
            f"action={action.value}, violations={[v.value for v in violations]}, "
            f"severity={severity_score}"
        )

        return result

    def _check_profanity(self, content: str) -> Dict[str, Any]:
        """Check content for profanity."""
        content_lower = content.lower()

        # Remove special characters for better detection
        clean_content = re.sub(r'[^a-z0-9\s]', '', content_lower)

        profanity_count = 0
        detected_words = []

        for word in self.profanity_words:
            if word in clean_content:
                profanity_count += 1
                detected_words.append(word)

        # Check for leetspeak and obfuscation
        obfuscated_count = self._check_obfuscated_profanity(clean_content)
        profanity_count += obfuscated_count

        has_profanity = profanity_count > 0
        severity = min(profanity_count * 2, 10)

        return {
            "has_profanity": has_profanity,
            "count": profanity_count,
            "detected_words": detected_words,
            "severity": severity
        }

    async def _check_spam(
        self,
        content: str,
        user_id: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check content for spam patterns."""
        is_spam = False
        severity = 0
        reasons = []

        # Check for URL spam
        url_count = len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content))
        if url_count > 2:
            is_spam = True
            severity += url_count
            reasons.append("excessive_urls")

        # Check for excessive repetition
        words = content.split()
        if len(words) > 5:
            unique_words = len(set(words))
            repetition_ratio = unique_words / len(words)
            if repetition_ratio < 0.3:
                is_spam = True
                severity += 3
                reasons.append("word_repetition")

        # Check for promotional patterns
        promo_patterns = [
            r'\b(buy|sell|cheap|discount|free|win|prize|money)\b',
            r'\b(click|visit|check out|limited time)\b',
            r'\b(\$|€|£|\d+\s*(dollars?|euros?|pounds?))\b'
        ]

        promo_matches = 0
        for pattern in promo_patterns:
            if re.search(pattern, content.lower()):
                promo_matches += 1

        if promo_matches >= 2:
            is_spam = True
            severity += promo_matches
            reasons.append("promotional_content")

        return {
            "is_spam": is_spam,
            "severity": severity,
            "reasons": reasons
        }

    def _check_excessive_caps(self, content: str) -> Dict[str, Any]:
        """Check for excessive capital letters."""
        if len(content) < 10:
            return {"excessive": False, "severity": 0}

        caps_count = sum(1 for c in content if c.isupper())
        caps_percentage = (caps_count / len(content)) * 100

        excessive = caps_percentage > self.rate_limits["caps_percentage"]
        severity = int(caps_percentage / 20) if excessive else 0

        return {
            "excessive": excessive,
            "percentage": caps_percentage,
            "severity": severity
        }

    async def _check_repeated_content(self, content: str, user_id: str) -> Dict[str, Any]:
        """Check for repeated content from the same user."""
        if not self.redis_pool:
            return {"is_repeated": False, "severity": 0}

        # Create content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()
        user_content_key = f"moderation:user_content:{user_id}"

        # Check recent content
        recent_hashes = await self.redis_pool.redis_client.lrange(user_content_key, 0, 10)
        repeat_count = recent_hashes.count(content_hash.encode())

        # Store current content hash
        await self.redis_pool.redis_client.lpush(user_content_key, content_hash)
        await self.redis_pool.redis_client.ltrim(user_content_key, 0, 20)
        await self.redis_pool.redis_client.expire(user_content_key, 3600)

        is_repeated = repeat_count >= self.rate_limits["duplicate_threshold"]
        severity = repeat_count * 2 if is_repeated else 0

        return {
            "is_repeated": is_repeated,
            "repeat_count": repeat_count,
            "severity": severity
        }

    async def _check_rate_limiting(self, user_id: str) -> Dict[str, Any]:
        """Check if user is exceeding rate limits."""
        if not self.redis_pool:
            return {"rate_limited": False, "severity": 0}

        current_time = datetime.utcnow()

        # Check messages per minute
        minute_key = f"moderation:rate:{user_id}:minute:{current_time.minute}"
        minute_count = await self.redis_pool.redis_client.incr(minute_key)
        await self.redis_pool.redis_client.expire(minute_key, 60)

        # Check messages per hour
        hour_key = f"moderation:rate:{user_id}:hour:{current_time.hour}"
        hour_count = await self.redis_pool.redis_client.incr(hour_key)
        await self.redis_pool.redis_client.expire(hour_key, 3600)

        rate_limited = (
            minute_count > self.rate_limits["messages_per_minute"] or
            hour_count > self.rate_limits["messages_per_hour"]
        )

        severity = 0
        if minute_count > self.rate_limits["messages_per_minute"]:
            severity += 5
        if hour_count > self.rate_limits["messages_per_hour"]:
            severity += 3

        return {
            "rate_limited": rate_limited,
            "minute_count": minute_count,
            "hour_count": hour_count,
            "severity": severity
        }

    async def _apply_custom_rules(
        self,
        content: str,
        context: Optional[Dict[str, Any]]
    ) -> List[ViolationType]:
        """Apply custom moderation rules."""
        violations = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check pattern matching
            if rule.pattern and re.search(rule.pattern, content, re.IGNORECASE):
                violations.append(rule.violation_type)

            # Check keyword matching
            content_lower = content.lower()
            for keyword in rule.keywords:
                if keyword.lower() in content_lower:
                    violations.append(rule.violation_type)
                    break

        return violations

    def _determine_action(
        self,
        violations: List[ViolationType],
        severity_score: int,
        user_rep: UserReputation
    ) -> ModerationAction:
        """Determine moderation action based on violations and user reputation."""
        if not violations:
            return ModerationAction.ALLOW

        # Adjust severity based on user reputation
        adjusted_severity = severity_score

        if user_rep.status == UserStatus.WARNING:
            adjusted_severity += 2
        elif user_rep.status == UserStatus.RESTRICTED:
            adjusted_severity += 4
        elif user_rep.status in [UserStatus.SUSPENDED, UserStatus.BANNED]:
            return ModerationAction.BLOCK

        # Lower trust users get stricter treatment
        if user_rep.trust_level <= 2:
            adjusted_severity += 1

        # Determine action based on adjusted severity
        if adjusted_severity >= 10:
            return ModerationAction.BAN_USER
        elif adjusted_severity >= 7:
            return ModerationAction.BLOCK
        elif adjusted_severity >= 5:
            return ModerationAction.WARN
        elif adjusted_severity >= 3:
            return ModerationAction.FLAG
        else:
            return ModerationAction.ALLOW

    async def _get_user_reputation(self, user_id: str) -> UserReputation:
        """Get user reputation from cache or database."""
        if user_id in self.user_reputations:
            return self.user_reputations[user_id]

        # Load from Redis cache
        if self.redis_pool:
            rep_key = f"moderation:reputation:{user_id}"
            rep_data = await self.redis_pool.redis_client.hgetall(rep_key)

            if rep_data:
                reputation = UserReputation(
                    user_id=user_id,
                    reputation_score=int(rep_data.get(b'reputation_score', 100)),
                    total_messages=int(rep_data.get(b'total_messages', 0)),
                    flagged_messages=int(rep_data.get(b'flagged_messages', 0)),
                    warnings_received=int(rep_data.get(b'warnings_received', 0)),
                    status=UserStatus(rep_data.get(b'status', b'good_standing').decode()),
                    trust_level=int(rep_data.get(b'trust_level', 1))
                )
                self.user_reputations[user_id] = reputation
                return reputation

        # Create new reputation
        reputation = UserReputation(user_id=user_id)
        self.user_reputations[user_id] = reputation
        return reputation

    async def _update_user_reputation(
        self,
        user_id: str,
        violations: List[ViolationType],
        severity_score: int
    ):
        """Update user reputation based on violations."""
        reputation = await self._get_user_reputation(user_id)
        reputation.total_messages += 1

        if violations:
            reputation.flagged_messages += 1
            reputation.reputation_score -= severity_score
            reputation.last_violation = datetime.utcnow()

            # Update status based on reputation
            if reputation.reputation_score <= 0:
                reputation.status = UserStatus.BANNED
            elif reputation.reputation_score <= 25:
                reputation.status = UserStatus.SUSPENDED
                reputation.suspension_until = datetime.utcnow() + timedelta(days=7)
            elif reputation.reputation_score <= 50:
                reputation.status = UserStatus.RESTRICTED
            elif reputation.reputation_score <= 75:
                reputation.status = UserStatus.WARNING

        else:
            # Gradually improve reputation for good behavior
            reputation.reputation_score = min(100, reputation.reputation_score + 1)

        # Update trust level
        if reputation.total_messages >= 100 and reputation.flagged_messages < 5:
            reputation.trust_level = min(5, reputation.trust_level + 1)

        # Save to Redis cache
        if self.redis_pool:
            rep_key = f"moderation:reputation:{user_id}"
            rep_data = {
                "reputation_score": reputation.reputation_score,
                "total_messages": reputation.total_messages,
                "flagged_messages": reputation.flagged_messages,
                "warnings_received": reputation.warnings_received,
                "status": reputation.status.value,
                "trust_level": reputation.trust_level
            }
            await self.redis_pool.redis_client.hset(rep_key, mapping=rep_data)
            await self.redis_pool.redis_client.expire(rep_key, 86400)  # 24 hours

    async def _create_moderation_case(
        self,
        user_id: str,
        content: str,
        violations: List[ViolationType],
        severity_score: int,
        auto_action: ModerationAction
    ):
        """Create moderation case for manual review."""
        case_id = f"case_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id}"

        case = ModerationCase(
            case_id=case_id,
            user_id=user_id,
            content=content,
            violation_type=violations[0] if violations else ViolationType.SPAM,
            severity_score=severity_score,
            auto_action=auto_action
        )

        # Store case in Redis for review queue
        if self.redis_pool:
            case_key = f"moderation:cases:{case_id}"
            case_data = {
                "case_id": case.case_id,
                "user_id": case.user_id,
                "content": case.content,
                "violation_type": case.violation_type.value,
                "severity_score": case.severity_score,
                "auto_action": case.auto_action.value,
                "status": case.status,
                "created_at": case.created_at.isoformat()
            }

            await self.redis_pool.redis_client.hset(case_key, mapping=case_data)
            await self.redis_pool.redis_client.expire(case_key, 604800)  # 7 days

            # Add to review queue
            await self.redis_pool.redis_client.lpush("moderation:review_queue", case_id)

    def _load_profanity_list(self) -> Set[str]:
        """Load profanity word list."""
        # Basic profanity list - in production, this would be loaded from a comprehensive database
        return {
            "damn", "hell", "crap", "stupid", "idiot", "moron", "dumb",
            "hate", "kill", "die", "murder", "threat", "violence"
        }

    def _load_spam_patterns(self) -> List[str]:
        """Load spam detection patterns."""
        return [
            r'\b(viagra|cialis|lottery|winner|congratulations)\b',
            r'\b(make money|work from home|get rich|easy money)\b',
            r'\b(click here|visit now|limited time|act now)\b'
        ]

    def _check_obfuscated_profanity(self, content: str) -> int:
        """Check for obfuscated profanity (leetspeak, special characters)."""
        # Simple leetspeak detection
        leetspeak_map = {
            '4': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's',
            '7': 't', '@': 'a', '$': 's', '!': 'i'
        }

        decoded_content = content
        for leet, normal in leetspeak_map.items():
            decoded_content = decoded_content.replace(leet, normal)

        # Check decoded content against profanity list
        count = 0
        for word in self.profanity_words:
            if word in decoded_content:
                count += 1

        return count

    async def _load_moderation_rules(self):
        """Load moderation rules from database or configuration."""
        # Default rules - in production, these would be loaded from database
        self.rules = [
            ModerationRule(
                rule_id="no_personal_info",
                name="No Personal Information",
                violation_type=ViolationType.PERSONAL_INFO,
                pattern=r'\b(\d{3}-\d{2}-\d{4}|\d{3}\.\d{2}\.\d{4})\b',  # SSN pattern
                action=ModerationAction.BLOCK,
                severity=8
            ),
            ModerationRule(
                rule_id="no_hate_speech",
                name="No Hate Speech",
                violation_type=ViolationType.HATE_SPEECH,
                keywords=["racist", "sexist", "homophobic", "bigot"],
                action=ModerationAction.BLOCK,
                severity=9
            ),
            ModerationRule(
                rule_id="no_harassment",
                name="No Harassment",
                violation_type=ViolationType.HARASSMENT,
                keywords=["kill yourself", "kys", "neck yourself"],
                action=ModerationAction.BAN_USER,
                severity=10
            )
        ]

    async def _load_user_reputations(self):
        """Load user reputations from cache."""
        # This would load frequently accessed user reputations from Redis
        pass

    async def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get user moderation status and reputation."""
        reputation = await self._get_user_reputation(user_id)

        return {
            "user_id": user_id,
            "reputation_score": reputation.reputation_score,
            "status": reputation.status.value,
            "trust_level": reputation.trust_level,
            "total_messages": reputation.total_messages,
            "flagged_messages": reputation.flagged_messages,
            "warnings_received": reputation.warnings_received,
            "last_violation": reputation.last_violation.isoformat() if reputation.last_violation else None,
            "suspension_until": reputation.suspension_until.isoformat() if reputation.suspension_until else None
        }

    async def get_moderation_stats(self) -> Dict[str, Any]:
        """Get overall moderation statistics."""
        if not self.redis_pool:
            return {"error": "Statistics not available without Redis"}

        # Get queue length
        queue_length = await self.redis_pool.redis_client.llen("moderation:review_queue")

        # Get today's stats
        today = datetime.utcnow().date().isoformat()
        stats_key = f"moderation:stats:{today}"
        daily_stats = await self.redis_pool.redis_client.hgetall(stats_key)

        return {
            "review_queue_length": queue_length,
            "daily_stats": {
                "total_moderated": int(daily_stats.get(b'total_moderated', 0)),
                "blocked_content": int(daily_stats.get(b'blocked_content', 0)),
                "flagged_content": int(daily_stats.get(b'flagged_content', 0)),
                "user_warnings": int(daily_stats.get(b'user_warnings', 0)),
                "user_bans": int(daily_stats.get(b'user_bans', 0))
            }
        }


# Global service instance
_moderation_service: Optional[ContentModerationService] = None


async def get_moderation_service(db_session: AsyncSession) -> ContentModerationService:
    """Get moderation service instance."""
    global _moderation_service

    if _moderation_service is None:
        redis_pool = None
        if get_redis_pool:
            try:
                redis_pool = await get_redis_pool()
            except Exception:
                pass

        _moderation_service = ContentModerationService(db_session, redis_pool)
        await _moderation_service.initialize()

    return _moderation_service