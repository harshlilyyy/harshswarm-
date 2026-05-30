# =============================================================================
# AGENT PROFILE — Psychological & Demographic Attributes
# =============================================================================
"""
Defines the complete psychological profile of an agent including:
- Demographics (age, gender, education, income, location)
- Big Five personality traits (OCEAN model)
- Schwartz value orientations (10 basic values)
- Goals, beliefs, and identity markers
- Resource constraints (time, money, energy, attention)

All traits are scientifically grounded in psychological research.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum, auto


class EducationLevel(Enum):
    """Educational attainment levels."""
    LESS_THAN_HS = "Less than high school"
    HS_DIPLOMA = "High school diploma"
    SOME_COLLEGE = "Some college"
    ASSOCIATES = "Associate's degree"
    BACHELORS = "Bachelor's degree"
    MASTERS = "Master's degree"
    DOCTORATE = "Doctorate"
    PROFESSIONAL = "Professional degree"


class EmploymentStatus(Enum):
    """Employment categories."""
    EMPLOYED_FULL_TIME = "Employed full-time"
    EMPLOYED_PART_TIME = "Employed part-time"
    SELF_EMPLOYED = "Self-employed"
    UNEMPLOYED = "Unemployed"
    STUDENT = "Student"
    RETIRED = "Retired"
    HOMEMAKER = "Homemaker"
    DISABLED = "Disabled"


@dataclass
class BigFive:
    """
    Big Five personality traits (OCEAN model).
    
    Each trait is a float in [0, 1] where:
    - 0.0 = extremely low
    - 0.5 = average/neutral
    - 1.0 = extremely high
    
    Traits:
    - Openness: Imagination, curiosity, creativity vs. conventionality
    - Conscientiousness: Organization, dependability, discipline vs. spontaneity
    - Extraversion: Sociability, assertiveness, energy from others vs. solitude
    - Agreeableness: Compassion, cooperation, trust vs. skepticism
    - Neuroticism: Emotional instability, anxiety, moodiness vs. stability
    """
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    
    def __post_init__(self):
        """Validate and clamp all traits to [0, 1]."""
        for trait_name in ['openness', 'conscientiousness', 'extraversion', 
                           'agreeableness', 'neuroticism']:
            val = getattr(self, trait_name)
            setattr(self, trait_name, max(0.0, min(1.0, val)))
    
    def to_dict(self) -> Dict[str, float]:
        """Return traits as dictionary."""
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'BigFive':
        """Create BigFive from dictionary."""
        return cls(
            openness=data.get('openness', 0.5),
            conscientiousness=data.get('conscientiousness', 0.5),
            extraversion=data.get('extraversion', 0.5),
            agreeableness=data.get('agreeableness', 0.5),
            neuroticism=data.get('neuroticism', 0.5)
        )


@dataclass
class SchwartzValues:
    """
    Schwartz Theory of Basic Values (10 universal values).
    
    Each value is a float in [0, 1] representing importance to the individual.
    
    Values (grouped by higher-order categories):
    
    Openness to Change:
    - Self-direction: Independent thought and action
    - Stimulation: Excitement, novelty, challenge
    
    Self-Enhancement:
    - Hedonism: Pleasure and sensuous gratification
    - Achievement: Personal success through competence
    - Power: Social status, dominance over resources
    
    Conservation:
    - Security: Safety, harmony, stability
    - Conformity: Restraint of actions that harm others
    - Tradition: Respect for customs and ideas
    
    Self-Transcendence:
    - Benevolence: Preserving welfare of close others
    - Universalism: Understanding, tolerance for all people/nature
    """
    self_direction: float = 0.5
    stimulation: float = 0.5
    hedonism: float = 0.5
    achievement: float = 0.5
    power: float = 0.5
    security: float = 0.5
    conformity: float = 0.5
    tradition: float = 0.5
    benevolence: float = 0.5
    universalism: float = 0.5
    
    def __post_init__(self):
        """Validate and clamp all values to [0, 1]."""
        for value_name in ['self_direction', 'stimulation', 'hedonism',
                           'achievement', 'power', 'security', 'conformity',
                           'tradition', 'benevolence', 'universalism']:
            val = getattr(self, value_name)
            setattr(self, value_name, max(0.0, min(1.0, val)))
    
    def to_dict(self) -> Dict[str, float]:
        """Return values as dictionary."""
        return {
            "self_direction": self.self_direction,
            "stimulation": self.stimulation,
            "hedonism": self.hedonism,
            "achievement": self.achievement,
            "power": self.power,
            "security": self.security,
            "conformity": self.conformity,
            "tradition": self.tradition,
            "benevolence": self.benevolence,
            "universalism": self.universalism
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'SchwartzValues':
        """Create SchwartzValues from dictionary."""
        return cls(
            self_direction=data.get('self_direction', 0.5),
            stimulation=data.get('stimulation', 0.5),
            hedonism=data.get('hedonism', 0.5),
            achievement=data.get('achievement', 0.5),
            power=data.get('power', 0.5),
            security=data.get('security', 0.5),
            conformity=data.get('conformity', 0.5),
            tradition=data.get('tradition', 0.5),
            benevolence=data.get('benevolence', 0.5),
            universalism=data.get('universalism', 0.5)
        )


@dataclass
class AgentProfile:
    """
    Complete demographic and psychological profile of an agent.
    
    This is the static configuration that defines who an agent IS,
    as opposed to dynamic state which defines what an agent FEELS/DOES.
    
    Attributes:
        # Identity
        id: Unique identifier
        name: Display name
        age: Age in years
        gender: Gender identity
        location: Geographic location (city, region, country)
        
        # Demographics
        education: Educational attainment
        employment: Employment status
        income_bracket: Income category (0-10 scale)
        socioeconomic_status: SES score (0-1)
        
        # Psychology
        big_five: Big Five personality traits
        schwartz_values: Schwartz value orientations
        
        # Beliefs & Goals
        political_leaning: Political orientation (-1 liberal to +1 conservative)
        religious_affiliation: Religious identity
        core_beliefs: List of fundamental belief statements
        short_term_goals: Current objectives (next days/weeks)
        long_term_goals: Life aspirations
        
        # Resources
        time_budget: Available time units per day
        money_budget: Available financial resources
        energy_level: Baseline energy capacity
        attention_capacity: Cognitive bandwidth
        
        # Social
        social_network_size: Number of social connections
        trust_radius: How many degrees of separation trusted
        group_memberships: Organizations/groups belonging to
    """
    # Identity
    id: str
    name: str
    age: int = 35
    gender: str = "not specified"
    location: str = "unspecified"
    
    # Demographics
    education: EducationLevel = EducationLevel.BACHELORS
    employment: EmploymentStatus = EmploymentStatus.EMPLOYED_FULL_TIME
    income_bracket: int = 5  # 0-10 scale
    socioeconomic_status: float = 0.5
    
    # Psychology
    big_five: BigFive = field(default_factory=BigFive)
    schwartz_values: SchwartzValues = field(default_factory=SchwartzValues)
    
    # Beliefs & Goals
    political_leaning: float = 0.0  # -1 to +1
    religious_affiliation: str = "none"
    core_beliefs: List[str] = field(default_factory=list)
    short_term_goals: List[str] = field(default_factory=list)
    long_term_goals: List[str] = field(default_factory=list)
    
    # Resources
    time_budget: float = 1.0  # Normalized daily capacity
    money_budget: float = 0.5  # Normalized financial resources
    energy_level: float = 0.7  # Baseline energy
    attention_capacity: float = 1.0  # Cognitive bandwidth
    
    # Social
    social_network_size: int = 150  # Dunbar's number baseline
    trust_radius: int = 2  # Degrees of separation
    group_memberships: List[str] = field(default_factory=list)
    
    # Additional metadata
    occupation: str = "unspecified"
    marital_status: str = "not specified"
    has_children: bool = False
    children_count: int = 0
    hobbies: List[str] = field(default_factory=list)
    media_preferences: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize profile to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "location": self.location,
            "education": self.education.value,
            "employment": self.employment.value,
            "income_bracket": self.income_bracket,
            "socioeconomic_status": self.socioeconomic_status,
            "big_five": self.big_five.to_dict(),
            "schwartz_values": self.schwartz_values.to_dict(),
            "political_leaning": self.political_leaning,
            "religious_affiliation": self.religious_affiliation,
            "core_beliefs": self.core_beliefs,
            "short_term_goals": self.short_term_goals,
            "long_term_goals": self.long_term_goals,
            "time_budget": self.time_budget,
            "money_budget": self.money_budget,
            "energy_level": self.energy_level,
            "attention_capacity": self.attention_capacity,
            "social_network_size": self.social_network_size,
            "trust_radius": self.trust_radius,
            "group_memberships": self.group_memberships,
            "occupation": self.occupation,
            "marital_status": self.marital_status,
            "has_children": self.has_children,
            "children_count": self.children_count,
            "hobbies": self.hobbies,
            "media_preferences": self.media_preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentProfile':
        """Create AgentProfile from dictionary."""
        # Handle nested objects
        big_five = BigFive.from_dict(data.get('big_five', {}))
        schwartz = SchwartzValues.from_dict(data.get('schwartz_values', {}))
        
        # Handle enums
        edu_str = data.get('education', 'Bachelor\'s degree')
        education = EducationLevel(edu_str) if edu_str in [e.value for e in EducationLevel] else EducationLevel.BACHELORS
        
        emp_str = data.get('employment', 'Employed full-time')
        employment = EmploymentStatus(emp_str) if emp_str in [e.value for e in EmploymentStatus] else EmploymentStatus.EMPLOYED_FULL_TIME
        
        return cls(
            id=data.get('id', 'unknown'),
            name=data.get('name', 'Anonymous'),
            age=data.get('age', 35),
            gender=data.get('gender', 'not specified'),
            location=data.get('location', 'unspecified'),
            education=education,
            employment=employment,
            income_bracket=data.get('income_bracket', 5),
            socioeconomic_status=data.get('socioeconomic_status', 0.5),
            big_five=big_five,
            schwartz_values=schwartz,
            political_leaning=data.get('political_leaning', 0.0),
            religious_affiliation=data.get('religious_affiliation', 'none'),
            core_beliefs=data.get('core_beliefs', []),
            short_term_goals=data.get('short_term_goals', []),
            long_term_goals=data.get('long_term_goals', []),
            time_budget=data.get('time_budget', 1.0),
            money_budget=data.get('money_budget', 0.5),
            energy_level=data.get('energy_level', 0.7),
            attention_capacity=data.get('attention_capacity', 1.0),
            social_network_size=data.get('social_network_size', 150),
            trust_radius=data.get('trust_radius', 2),
            group_memberships=data.get('group_memberships', []),
            occupation=data.get('occupation', 'unspecified'),
            marital_status=data.get('marital_status', 'not specified'),
            has_children=data.get('has_children', False),
            children_count=data.get('children_count', 0),
            hobbies=data.get('hobbies', []),
            media_preferences=data.get('media_preferences', [])
        )
