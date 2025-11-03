"""
Command-line interface for google-search-scraper
"""

import sys
import json
import argparse
from typing import Optional

from . import search, __version__
from .exceptions import GoogleSearchError


def print_results(result, format_type: str = 'text'):
    """Print search results in specified format"""
    if format_type == 'json':
        print(json.dumps(result.to_dict(), indent=2))
        return
    
    # Text format
    print("=" * 70)
    print(f"Query: {result.query}")
    print(f"Time: {result.search_time:.2f}s")
    print("=" * 70)
    
    if result.answer:
        print("\n📝 ANSWER:")
        print("-" * 70)
        answer_preview = result.answer[:500] + ('...' if len(result.answer) > 500 else '')
        print(answer_preview)
        print()
    
    print(f"🔗 TOP {len(result.urls)} RESULTS:")
    print("-" * 70)
    
    if result.urls:
        for i, url in enumerate(result.urls, 1):
            print(f"{i:2d}. {url}")
    else:
        print("No URLs found")
    
    # Display content if extracted
    if result.contents:
        print(f"\n📄 EXTRACTED CONTENT ({len(result.contents)} pages):")
        print("-" * 70)
        for i, content in enumerate(result.contents, 1):
            if content.error:
                print(f"\n{i}. {content.url}")
                print(f"   ✗ Error: {content.error}")
            else:
                print(f"\n{i}. {content.title or 'No title'}")
                print(f"   URL: {content.url}")
                print(f"   Words: {content.word_count}")
                if content.content:
                    preview = content.content[:200] + ('...' if len(content.content) > 200 else '')
                    print(f"   Preview: {preview}")
    
    print("=" * 70)


def save_results(result, filename: str):
    """Save results to file"""
    import time as time_module
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Query: {result.query}\n")
        f.write(f"Date: {time_module.strftime('%Y-%m-%d %H:%M:%S', time_module.localtime(result.timestamp))}\n")
        f.write(f"Duration: {result.search_time:.2f}s\n\n")
        
        if result.answer:
            f.write("ANSWER:\n" + "-"*50 + "\n")
            f.write(result.answer + "\n\n")
        
        f.write(f"URLs ({len(result.urls)}):\n" + "-"*50 + "\n")
        for i, url in enumerate(result.urls, 1):
            f.write(f"{i}. {url}\n")
    
    print(f"\n✓ Results saved to: {filename}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Fast Google search scraper with stealth mode',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  google-search "python tutorial"
  google-search "best restaurants" --max-results 20
  google-search "weather today" --no-answer --output results.txt
  google-search "machine learning" --format json > results.json
  google-search "data science" --visible --timeout 60000
        """
    )
    
    parser.add_argument(
        'query',
        type=str,
        nargs='?',
        help='Search query (if not provided, enters interactive mode)'
    )
    
    parser.add_argument(
        '-n', '--max-results',
        type=int,
        default=10,
        metavar='N',
        help='Maximum number of results to return (default: 10)'
    )
    
    parser.add_argument(
        '--no-answer',
        action='store_true',
        help='Skip extracting Google\'s direct answer'
    )
    
    parser.add_argument(
        '--extract-content',
        action='store_true',
        help='Extract page content from each URL (slower but more detailed)'
    )
    
    parser.add_argument(
        '--visible',
        action='store_true',
        help='Run browser in visible mode (for debugging)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30000,
        metavar='MS',
        help='Page load timeout in milliseconds (default: 30000)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        metavar='FILE',
        help='Save results to file'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format: text or json (default: text)'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'google-search-scraper {__version__}'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress all output except results'
    )
    
    args = parser.parse_args()
    
    # Interactive mode if no query provided
    if not args.query:
        print("=" * 70)
        print(f"Google Search Scraper v{__version__}")
        print("=" * 70)
        query = input("\nSearch: ").strip()
        if not query:
            print("Error: Query required")
            sys.exit(1)
    else:
        query = args.query
    
    # Show progress unless quiet mode
    if not args.quiet:
        print(f"\nSearching for: '{query}'...")
    
    try:
        # Perform search
        result = search(
            query=query,
            max_results=args.max_results,
            extract_answer=not args.no_answer,
            extract_content=args.extract_content,
            headless=not args.visible,
            timeout=args.timeout
        )
        
        # Print results
        print_results(result, format_type=args.format)
        
        # Save to file if requested
        if args.output:
            if args.format == 'json':
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result.to_dict(), f, indent=2)
                print(f"\n✓ Results saved to: {args.output}")
            else:
                save_results(result, args.output)
        
    except GoogleSearchError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nSearch cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()