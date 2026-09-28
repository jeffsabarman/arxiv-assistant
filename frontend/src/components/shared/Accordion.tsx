import * as Collapsible from "@radix-ui/react-collapsible"
import { ChevronDown } from "lucide-react"
import { useState } from "react"

const animationStyle = `
          @keyframes slideDown {
            from { height: 0; opacity: 0; }
            to { height: var(--radix-collapsible-content-height); opacity: 1; }
          }
          @keyframes slideUp {
            from { height: var(--radix-collapsible-content-height); opacity: 1; }
            to { height: 0; opacity: 0; }
          }
        `

interface AccordionProps {
    title: React.ReactNode
    children: React.ReactNode
    defaultOpen?: boolean
}

const Accordion = ({ title, children, defaultOpen = false }: AccordionProps) => {
    const [open, setOpen] = useState(defaultOpen)

    return (
        <Collapsible.Root open={open} onOpenChange={setOpen}>
            <Collapsible.Trigger className="flex items-center gap-1 w-full cursor-pointer">
                {title}
                <ChevronDown
                    size={12}
                    className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`}
                />
            </Collapsible.Trigger>

            <Collapsible.Content
                style={{
                    overflow: "hidden",
                    animation: open ? "slideDown 0.2s ease-out" : "slideUp 0.2s ease-out",
                }}
            >
                {/* <style>{animationStyle}</style> */}
                <div className="mt-2">{children}</div>
            </Collapsible.Content>
        </Collapsible.Root>
    )
}

export default Accordion