#!/usr/bin/env python3
"""
Get class sections for SJSU courses
"""

from client import Sparq


def get_classes():
    """Get class sections for one or more courses."""
    print("\n" + "=" * 80)
    print("SPARQ - Get Class Sections")
    print("=" * 80)
    print("\nRetrieve available class sections for SJSU courses.")
    print("No API key required for this feature.\n")
    
    # Get course IDs from user
    print("Enter course ID(s) separated by commas (e.g., 'CS 49J' or 'CS 49J, MATH 42'):")
    course_input = input("> ").strip()
    
    if not course_input:
        print("\nError: At least one course ID is required.")
        return
    
    try:
        client = Sparq()
        
        print(f"\nFetching class sections for: {course_input}")
        print("Please wait...\n")
        
        result = client.classes(course_input)
        
        # Check if it's a message response (no sections found)
        if "message" in result:
            print(f"\n{result['message']}")
            return
        
        # Display results
        total_sections = 0
        for course_id, sections in result.items():
            section_count = len(sections)
            total_sections += section_count
            
            print("=" * 80)
            print(f"{course_id} - {section_count} section(s) available")
            print("=" * 80)
            
            if section_count == 0:
                print("No sections found for this course.\n")
                continue
            
            for i, section in enumerate(sections, 1):
                print(f"\n[Section {i}]")
                print(f"  Section:     {section.get('Section', 'N/A')}")
                print(f"  Class #:     {section.get('Class Number', 'N/A')}")
                print(f"  Title:       {section.get('Course Title', 'N/A')}")
                print(f"  Instructor:  {section.get('Instructor', 'N/A')}")
                print(f"  Mode:        {section.get('Mode of Instruction', 'N/A')}")
                print(f"  Type:        {section.get('Type', 'N/A')}")
                print(f"  Units:       {section.get('Units', 'N/A')}")
                print(f"  Days/Times:  {section.get('Days', 'N/A')} {section.get('Times', 'N/A')}")
                print(f"  Location:    {section.get('Location', 'N/A')}")
                print(f"  Dates:       {section.get('Dates', 'N/A')}")
                print(f"  Open Seats:  {section.get('Open Seats', 'N/A')}")
                
                if section.get('Satisfies'):
                    print(f"  Satisfies:   {section.get('Satisfies')}")
                
                if section.get('Notes'):
                    print(f"  Notes:       {section.get('Notes')}")
        
        print("\n" + "=" * 80)
        print(f"Total: {total_sections} section(s) across {len(result)} course(s)")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\nError: {e}\n")


if __name__ == "__main__":
    get_classes()
