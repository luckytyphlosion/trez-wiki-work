template = """{{#if:{{{A|}}}|{{coderow|A|{{{A|}}}}}}}"""

def main():
    output = ""

    output += template
    for letter in "BCDEFGHIJKLMNOPQRSTUVWXYZ":
        cur_template = template.replace("A", letter)
        output += cur_template

    output += "{{#if:{{{asterisk|}}}|{{coderow|*|{{{asterisk|}}}}}}}"
    with open("gen_coderows_out.txt", "w+") as f:
        f.write(output)

if __name__ == "__main__":
    main()
