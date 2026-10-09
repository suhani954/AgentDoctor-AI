import { AlertTriangle, CheckCircle2, Circle, Wrench } from "lucide-react";

function getIcon(eventType) {
  if (eventType === "error") return AlertTriangle;
  if (eventType === "tool_call" || eventType === "tool") return Wrench;
  if (eventType === "output") return CheckCircle2;
  return Circle;
}

export default function ExecutionTimeline({ timeline }) {
  if (!timeline?.length) {
    return <div className="panel-message">No timeline events found.</div>;
  }

  return (
    <div className="timeline">
      {timeline.map((event) => {
        const Icon = getIcon(event.event_type);

        return (
          <div className="timeline-item" key={`${event.order}-${event.title}`}>
            <div className={`timeline-icon ${event.event_type}`}>
              <Icon size={16} />
            </div>

            <div className="timeline-content">
              <div className="timeline-header">
                <strong>{event.title}</strong>
                <span>{event.event_type}</span>
              </div>

              {event.content && <p>{event.content}</p>}

              {event.metadata && Object.keys(event.metadata).length > 0 && (
                <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}